import argparse
import collections
import copy
from itertools import accumulate
import json
from typing import Generic
from clearconf.api.node import is_config, is_hidden, is_private, is_type
from clearconf.api.types import Prompt
import tempfile
import os
import importlib
import sys
import inspect


def arg_parse(config):
    from clearconf.api._utils.misc import subclass

    parser = argparse.ArgumentParser()
    
    flat_config = config.to_flat_dict()

    config_attrs = []
    for k in flat_config:
        parts = k.split('.')
        config_attrs.extend(accumulate(parts, lambda a, b: a + '.' + b))

    leaves_counter = collections.Counter([k.split('.')[-1] for k in config_attrs])
    config_attrs = set(config_attrs)

    for key in config_attrs:
        short_key = key.split('.')[-1]
        options = [f'--{key}'] 
        options += [f'--{short_key}'] if leaves_counter[short_key] == 1 else []
        parser.add_argument(*options)
    
    args = parser.parse_args()
    
    for key, value in vars(args).items():
        if value is None:
            continue

        parts = key.split('.')
        nested_cfg = config
        for part in parts[:-1]:
            nested_cfg = getattr(config, part)
        
        n_value = getattr(nested_cfg, parts[-1])
        n_name = parts[-1]
        # Node API should be removed and helper methods placed inside ._cc attribute
        if is_config(n_value, n_name, nested_cfg):
            # import class and make it superclass
            idx = -value[::-1].find('.')
            config_superclass = getattr(importlib.import_module(value[:idx-1]), value[idx:])
            # When we do this the meta constructor gets called again
            # Is it an issue in practice? Maybe it is even a good thing?
            if Generic in (base_classes := n_value.mro()): base_classes.remove(Generic)
            superclassed_config = type(n_name, tuple(base_classes[:-1]) + (config_superclass,) ,
                 dict(list(dict(vars(config_superclass)).items()) + list(dict(vars(getattr(nested_cfg, n_name))).items())))
    
            # node.value._name = f'{node.value._name}:{config_superclass.__name__}'
            setattr(nested_cfg, n_name, superclassed_config)

        else:
            setattr(nested_cfg, n_name, value)


def user_input(config):

    class any_prompt:
        """Find all Prompts type in the tree"""
        def compute(value, name, parent):
            if is_type(value, name, parent, Prompt):
                return [(value, name, parent)]
            else:
                return []

        def aggregate(res1, res2):
            return res1 + res2

    prompt_field = config._apply(any_prompt)

    if len(prompt_field) == 0:
        return

    user_input = {}
    content = ''
    for field in prompt_field:
        content += f'user_input["{field[1]}"] = {repr(field[0])}\n'

    # Create a temporary file with a .py extension and write the content of the source file to it
    with tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w') as tmp_file:
        tmp_file_name = tmp_file.name
        module_name = os.path.basename(tmp_file_name).rsplit('.', 1)[0]
        tmp_file.write(content)

    # Check if $EDITOR is set, otherwise use vim
    editor = os.environ.get('EDITOR', 'vim')
    # Open the temporary file with the editor
    os.system(f"{editor} {tmp_file_name}")

    # Read the content of the file after editing
    with open(tmp_file_name, 'r') as tmp_file:
        user_values = tmp_file.read()
    exec(user_values)

    for field in prompt_field:
        field[0] = user_input[field[1]]


@classmethod
def to_dict2(cls, add_parent=False):
    target = cls

    # This add target as the top key of the dictionary
    #  if add_parent is True
    res = output = {}
    if add_parent:
        key = target.__name__
        if len(target.mro()) >= 4:
            key =  target.mro()[2].__name__
        if len(target.mro()) >= 5:
            key = f'{key}({target.mro()[3].__name__})'
        output = {key: res}

    target_attr = copy.deepcopy(dir(target))
    # This removes variables from superclasses
    for attr in [a for a in target.mro() 
                    if a.__name__ not in [target.__name__, f'{target.__name__}_mod', target.__name__[:-4], 'BaseConfig', 'Config', 'object']]:
        # The allows inheritance between configs but I guess there are better solutions
        if 'configs' not in attr.__module__:
            target_attr = list(filter(lambda x: x not in dir(attr), target_attr))

    for k in target_attr:
        if not k.startswith('_') and k not in ['to_dict', 'to_dict2', 'to_json', 'to_list', 'init', 'to_flat_dict', 'get_cfg', 'parent']:
            attr = getattr(target, k)
            
            if type(attr).__name__ == 'property':
                attr = attr.fget

            # If it's a module get inside
            if hasattr(attr, '__module__'):

                # If it's a class inside config, get inside it,
                # else just log module and name in the dict as a string.

                # if we are executing the config the module is __main__. If we are importing it is config
                if type(attr).__name__ == 'function':
                    if attr.__name__ == '<lambda>':
                        funcString = str(inspect.getsourcelines(attr)[0])
                        res[k] = funcString.strip("['\\n']").split(" = ")[1]
                    else:
                        res[k] = f'function: {attr.__name__}'
                elif attr.__module__.split('.')[0] == '__main__' or 'config' in attr.__module__:
                    if not inspect.isclass(attr): attr = type(attr)
                    
                    subclass_names = [a for a in [a.__name__ for a in attr.mro()] 
                                    if a not in [k, 'BaseConfig', 'object']]
                    
                    if len(subclass_names) > 0: # when a config class is subclassed to use it directly
                        k = f'{k}({subclass_names[0]})'

                    res[k] = attr.to_dict()
                else:
                    # End up here if attr is not a class defined inside module.
                    if type(attr).__name__ == 'type':  # it is a class
                        name = f'{attr.__module__}.{attr.__name__}'
                    else: # it is an object
                        if attr.__str__ is not object.__str__:
                            name = attr.__str__()  # sometimes repr() might be preferable
                        else:
                            name = f'{type(attr).__name__}.{attr.__name__}'
                        res[k] = name
            # If it's not a class save it. This is done for basic types.
            # Could cause problems with complex objects
            else:
                res[k] = attr

    return output

@classmethod
def to_flat_dict(cls) -> dict:
    res = cls.to_dict2()
    res = flatten(res)
    return res

@classmethod
def to_list(cls):
    target = cls

    res = []
    for k in dir(target):
        if not k.startswith('_') and k not in ['to_dict', 'to_json', 'to_dict2', 'to_list', 'init', 'to_flat_dict', 'get_cfg', 'parent']:
            attr = getattr(target, k)
            # If it's a class inside config, get inside it,
            # else just log module and name in the dict as a string
            if type(attr) == type:
                if attr.__module__.split('.')[0] in ['configs', '__main__']:
                    res.append(attr.to_list())
                else:
                    res.append(f'{attr.__module__}.{attr.__name__}')
            # If it's not a class save it. This is done for basic types.
            # Could cause problems with complex objects
            else:
                res.append(attr)
    return res



@classmethod
def to_json(cls):
    return json.dumps(cls.to_dict())

@classmethod
def to_dict(cls):
    res = {}
    
    for name in dir(cls):
        value = getattr(cls, name)
        
        if not is_private(value, name, cls) and not is_hidden(value, name, cls):
            if is_config(value, name, cls):
                res[value._cc.name] = value.to_dict()   
            else:
                res[name] = str(value)  # doing this automatically resolve eval strings
    return res
        

def get_cfg(self, to_self=False):
    if not to_self:
        return self.__class__
    
    target = self.__class__
    
    target_attr = dir(target)
    # This removes variables from superclasses
    for attr in [a for a in target.mro() 
                    if a.__name__ not in [target.__name__, target.__name__[:-4], 'BaseConfig', 'Config', 'object']]:
        # The allows inheritance between configs but I guess there are better solutions
        if 'configs' not in attr.__module__:
            target_attr = list(filter(lambda x: x not in dir(attr), target_attr))
    
    for k in target_attr:
        if not k.startswith('_') and k not in ['to_dict', 'to_dict2', 'to_json', 'to_list', 'init', 'to_flat_dict', 'get_cfg', 'parent']:
            attr = getattr(target, k)
            setattr(self, k, attr)

# def __getattribute__(self, item):
#     return object.__getattribute__(self, item)


def flatten(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)