#####################################################################
#                                 DOC                               #
#####################################################################

"""
@author: F. Ramognino       <federico.ramognino@polimi.it>
Last update:        12/06/2023
"""

#####################################################################
#                               IMPORT                              #
#####################################################################


from ..Utilities import Utilities
from collections import OrderedDict

from types import ModuleType
from typing import TypeVar, Iterable, Any, _SpecialGenericAlias
T = TypeVar("T")

import os.path as path

from libICEpost.src.base.Functions.typeChecking import checkType

#############################################################################
#                               MAIN CLASSES                                #
#############################################################################

class Dictionary(OrderedDict, Utilities):
    """
    Ordered dictionary embedding some useful OpenFOAM-like methods.
    """
    path:str|None
    file:str|None
    
    #############################################################################
    def __init__(self, *args, _fileName:str=None, **argv):
        """
        Same constructor as collections.OrderedDict class.
        """
        if _fileName is None:
            # no file assosiaction
            self.fileName = None
            self.path = None
        else:
            #Relative  or absolute path
            base, file = path.split(_fileName)
            
            #Path
            if (base == "") or (base is None):
                self.path = "." + path.sep
            else:
                self.path = base
            
            #File name:
            if (file == "") or (file is None):
                raise ValueError(f"Invalid file name {_fileName}")
            self.fileName = file
        
        super().__init__(*args,**argv)
        
    #############################################################################
    @classmethod
    def fromFile(cls, fileName:str):
        """
        Read the variables stored in a python file (Runs the code in the file and retrieves the local variables)
        
        Args:
            fileName (str): Path of the file
            
        Returns:
            Dictionary: A Dictionary object containing the variables defined in the file.
        """
        checkType(fileName, str, "fileName")
        
        this = cls(_fileName=fileName)
        
        _LOCALS = locals().copy()
        _OLDLOCALS = list(_LOCALS)
        
        with open(fileName) as _FILE:
            try:
                exec(compile(_FILE.read(), fileName, "exec"))
            except Exception as e:
                raise IOError(f"Error loading dictionary from file '{fileName}'")
        
        _LOCALS = locals().copy()
        for l in _LOCALS.keys():
            #If the variable is not a module and is not a local variable of the function, add to the dictionary
            if not l in (_OLDLOCALS + ["_OLDLOCALS", "_LOCALS", "_FILE"]) and (not isinstance(_LOCALS[l], ModuleType)):
                this[l] = _LOCALS[l]
            
        return this
        
    #############################################################################
    def lookup(self, entryName:str, *, varType:T|Iterable[type]=None, **kwargs) -> T|Any:
        """
        Same as __getitem__ but embeds error handling and type checking.

        Args:
            entryName (str): Name of the entry to look for
            varType (type|Iterable[type], optional): Type of the variable to lookup for. 
                Performes type-checking if it is given. Defaults to None.
            **kwargs (dict[str,object]): Additional arguments to pass to the checkType function in case of type checking.

        Raises:
            KeyError: If the entry is not found
            TypeError: If the type is not consistent with varType
            
        Returns:
            varType|Any: self[entryName]
        """
        checkType(entryName, str, "entryName")
        
        if not entryName in self:
            raise KeyError(f"Entry '{entryName}' not found in Dictionary. Available entries are:\n\t" + f"\n\t".join([str(k) for k in self.keys()]))
        elif not (varType is None):
            checkType(self[entryName], varType, entryName, **kwargs)

        return self[entryName]
    
    #############################################################################
    def pop(self, entryName:str):
        """
        entryName:  str
            Name of the entry to look for
        
        Same as dictionary.pop but custom error message
        """
        if not entryName in self:
            raise KeyError(f"Entry '{entryName}' not found in Dictionary. Available entries are:\n\t" + "\n\t".join([str(k) for k in self.keys()]))
        else:
            return super().pop(entryName)
    
    ######################################
    def lookupOrDefault(self, entryName:str, default:T, fatal:bool=True, **kwargs) -> T:
        """
        Lookup of give a default value if not found
        
        Args:
            entryName (str): Name of the entry to look for
            default (T): Instance to return in case the value is not found. It is also used for typeChecking
            fatal (bool, optional): If the type is not consistent rise a TypeError. Defaults to True.
            **kwargs (dict[str,object]): Additional arguments to pass to the checkType function in case of type checking.
            
        Returns:
            T: self[entryName] if entryName is found, else default
        """
        checkType(entryName, str, "entryName")
        checkType(fatal, bool, "fatal")
        
        if not entryName in self:
            return default
        else:
            if fatal:
                #Check the type of the entry
                checkType(self[entryName], type(default), entryName, **kwargs)
            return self[entryName]
    
    ######################################
    def _correctSubdicts(self):
        """
        Convert recursively every subdictionary into Dictionary classes.
        """
        for entry in self:
            if isinstance(self[entry], dict) and not isinstance(self[entry], Dictionary):
                self[entry] = Dictionary(**self[entry])
        return self
    
    ######################################
    def __setitem__(self, *args, **argv):
        super().__setitem__(*args, **argv)
        self._correctSubdicts()
        return self
    
    ######################################
    def update(self, /, dictionary:dict=None, **kwargs):
        """
        Performs like dict.update() method but recursively updates sub-dictionaries. 
        Accepts both a dictionary and keyword arguments.
        
        Args:
            dictionary (dict, optional): Dictionary to update with. Defaults to None.
        """
        if not dictionary is None:
            self.update(**dictionary)
            
        for key in kwargs:
            if (isinstance(kwargs[key],dict) if (key in self) else False):
                self[key].update(**kwargs[key])
            else:
                super().update({key:kwargs[key]})
                
        self._correctSubdicts()
        
        return self
