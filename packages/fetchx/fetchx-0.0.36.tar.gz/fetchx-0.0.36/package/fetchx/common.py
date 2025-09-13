import datetime

from .generaltypes import __itemList__, HttpBody
from .ioutils import save_json

import json
import base64
from enum import Enum
from typing import Dict, List
from types import SimpleNamespace
import math
from numbers import Number
import httpx


class RestMethod(Enum):
    """

    """
    GET = "GET"
    POST = "POST"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

    def __str__(self):
        if self == RestMethod.GET:
            return "GET"
        elif self == RestMethod.POST:
            return "POST"
        elif self == RestMethod.OPTIONS:
            return "OPTIONS"
        elif self == RestMethod.HEAD:
            return "HEAD"
        elif self == RestMethod.PUT:
            return "PUT"
        elif self == RestMethod.DELETE:
            return "DELETE"
        elif self == RestMethod.PATCH:
            return "PATCH"
        else:
            return "UNKNOWN"


class JsonObject(SimpleNamespace):
    """
    Class which can be initialized from dictionary and can be converted back to dictionary
    """   
    def __init__(self, raw_json_input: dict | list, **kwargs):
        """
        Initializes JsonObject from dictionary
        Allows users to access dictionary items as object properties
        Can parse dictionaries like this:{"b": 2, "a": 1, 
        "%$@$*&@#%*& @%@#% - ": "None", "c": {"d": 3, "e": [4, [5, [[6]]],
        {"test": "test"}]}, "f": [7, None, {"property": None}, 9]}
        :param raw_json_input: dictionary to be converted to uuJsonObject
        :param kwargs: additional arguments to be passed to SimpleNamespace
        """
        def _init_list(items: list):
            # helper function to initialize list
            result = ListX()
            for item in items:
                if isinstance(item, dict):
                    result.append(JsonObject(item))
                elif isinstance(item, list):
                    result.append(_init_list(item))
                else:
                    result.append(item)
            return result
                    
        # Initialize parent class
        super().__init__(**kwargs)
        # remember order of attributes
        self.__attr_original_order__ = []
        updated_input = uuDict(raw_json_input)
        # for each item in dictionary
        for key, value in updated_input.items():
            # remember order of attributes
            self.__attr_original_order__.append(key)
            # if value is dictionary then convert it to uuJsonObject
            if isinstance(value, dict):
                self.__setattr__(key, JsonObject(value))
            # if value is list then convert each item in list
            elif isinstance(value, list):
                new_value = _init_list(value)
                self.__setattr__(key, new_value)
            # otherwise just set the value
            else:
                self.__setattr__(key, value)
    
    def _list_to_dict(self, items: list, force_convert_properties_to_str: bool = False) -> list:
        """
        Converts list of uuJsonObject to list of uuDict
        :param items:   list of uuJsonObject
        :return:        list of uuDict
        """
        result = []
        for item in items:
            if isinstance(item, JsonObject):
                result.append(item.to_dict(force_convert_properties_to_str=force_convert_properties_to_str))
            elif isinstance(item, list):
                result.append(self._list_to_dict(item, force_convert_properties_to_str=force_convert_properties_to_str))
            else:
                result.append(item if not force_convert_properties_to_str else str(item))
        return result
    
    def to_dict(self, force_convert_properties_to_str: bool = False) -> 'uuDict':
        """
        Converts uuJsonObject to uuDict
        :return:
        """
        result = {}
        property_names = [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))]
        for property_name in property_names:
            property = getattr(self, property_name)
            if isinstance(property, JsonObject):
                result[property_name] = property.to_dict(force_convert_properties_to_str=force_convert_properties_to_str)
            elif isinstance(property, list):
                result[property_name] = self._list_to_dict(property, force_convert_properties_to_str=force_convert_properties_to_str)
            elif isinstance(property, dict):
                result[property_name] = uuDict(property)
            else:
                result[property_name] = property if not force_convert_properties_to_str else str(property)
        # reorder attributes to original order
        final_result = {}
        for key in self.__attr_original_order__:
            if key in result.keys():
                final_result[key] = result[key]
                del result[key]
        for key, value in result.items():
            final_result[key] = value
        # create final result
        final_result = uuDict(final_result)
        final_result.indentation = 4
        return final_result
    
    def _to_string(self, indentation: int = 4, nested_level: int = 0, end_with_new_line: bool = False,
                  json_like_output: bool = False, force_convert_to_str: bool =False) -> str:
        value = self.to_dict()
        result = value._to_string(indentation, nested_level, end_with_new_line,
                                  json_like_output=json_like_output, force_convert_to_str=force_convert_to_str)
        return result

    def to_json_str(self, stringify: bool = False):
        result = self._to_string(indentation=4, json_like_output=True, force_convert_to_str=stringify)
        return result

    def to_str(self, stringify: bool = False):
        result = self._to_string(indentation=4, json_like_output=False, force_convert_to_str=stringify)
        return result

    def __str__(self):
        result = self.to_dict()
        return str(result)


class DataType(Enum):
    DICT = "__DICT__"
    LIST = "__LIST__"
    TEXT = "__TEXT__"
    BINARY = "__BASE64__"
    ERROR = "__ERROR__"
    NULL = "__NULL__"
    UNKNOWN = "__UNKNOWN__"

    def __str__(self):
        if self == DataType.DICT:
            return "__DICT__"
        elif self == DataType.LIST:
            return "__LIST__"
        elif self == DataType.TEXT:
            return "__TEXT__"
        elif self == DataType.BINARY:
            return "__BASE64__"
        elif self == DataType.ERROR:
            return "__ERROR__"
        # elif self == uuDictDataType.NULL:
        #     return "__NULL__"
        else:
            return "__UNKNOWN__"
        
    @staticmethod
    def from_str(value: str) -> 'DataType':
        if value == DataType.DICT.value:
            return DataType.DICT
        elif value == DataType.LIST.value:
            return DataType.LIST
        elif value == DataType.TEXT.value:
            return DataType.TEXT
        elif value == DataType.BINARY.value:
            return DataType.BINARY
        elif value == DataType.ERROR.value:
            return DataType.ERROR
        # elif value == uuDictDataType.NULL.value:
        #     return uuDictDataType.NULL
        else:
            return DataType.UNKNOWN


class uuDict(dict):

    def _load_dict_from_bytes(self, value: bytes, encoding: str = 'utf-8') -> str | dict | list:
        if (len(value) >= 65536000):
            return {DataType.BINARY.value: f'Use "binary" property to access binary content. '
                    f'The content is too large to process. It exceeds the maximum allowed size of 64MB.'}
        try:
            # Decode the response content into text
            result_str = value.decode(encoding=encoding)
            # try to decode content into dict
            try:
                result_json = json.loads(result_str)
                # converts list into dict
                if isinstance(result_json, (list, dict)):
                    return result_json
                else:
                    return {DataType.BINARY.value: f'Use "binary" property to access binary content. Cannot decode binary content using encoding "{encoding}".'}
            except:
                return result_str
        # if decoding fails then return as binary
        except:
            return {DataType.BINARY.value: f'Use "binary" property to access binary content. Cannot decode binary content using encoding "{encoding}".'}


    def __init__(self, *args, **kwargs):
        """
        Initialize the uuDict.
        You can call this constructor with a variety of input types, including:
        - A dictionary
        - A list
        - A string
        - A number
        - A boolean
        - None
        It always produces a valid dictionary.
        For example, if you pass a string, it will be converted to a dictionary {"__TEXT__": "your_string"}
        If you pass a number, it will be converted to a dictionary {"__TEXT__": "your_number"}
        If you pass a list, it will be converted to a dictionary {"__LIST__": ["item1", "item2", ...]}
        If you pass a dictionary, it will be used as is.
        """
        # set default indentation
        self._indentation = 4
        # set default data type
        self._data_type = DataType.UNKNOWN
        # set default binary
        self._binary = None
        # determine value from args and kwargs
        if isinstance(args, tuple) and len(args) == 1:
            value = args[0]
        elif isinstance(args, tuple) and len(kwargs) > 0:
            value = dict(*args, **kwargs)
        elif isinstance(args, tuple) and len(args) == 0:
            value = None
        else:
            value = error_message("Cannot determine value from given arguments")

        # If value is None, initialize with an empty text
        if value is None:
            super(uuDict, self).__init__({DataType.TEXT.value: ""})
            self._determine_data_type()
            return
        # if args is of type bytes
        if isinstance(value, (bytes, bytearray)):
            # Initialize binary content
            self._binary = value
            # Determine encoding
            encoding = 'utf-8'
            if kwargs is not None and 'encoding' in kwargs.keys():
                encoding = kwargs['encoding']
            # Load the dictionary from the binary content
            value = self._load_dict_from_bytes(value, encoding=encoding)
        # if args is a single string or number (int, float, complex) or bool then convert it to dictionary with text
        if isinstance(value, (str, Number, bool)):
            super(uuDict, self).__init__({DataType.TEXT.value: str(value)})
            self._determine_data_type()
            return
        # if args is a single list then convert it to dictionary with itemList
        if isinstance(value, list):
            value = {DataType.LIST.value: ListX(value)}
        # if args is a single dictionary then use it as is
        if isinstance(value, dict):
            super(uuDict, self).__init__({})
            # convert all nested dictionaries to uuDict
            for k, v in value.items():
                if isinstance(v, dict):
                    self[k] = uuDict(v)
                elif isinstance(v, list):
                    self[k] = ListX(v)
                else:
                    self[k] = v
        else:
            self[DataType.ERROR.value] = f'Cannot initialize from value of type "{str(type(value))}".'
        # determine data type
        self._determine_data_type()

    def _determine_data_type(self):
        """
        Determine the data type of the uuDict.
        """
        # Get the first key
        key = next(iter(self.keys()), None)
        if key is None or key == DataType.DICT.value:
            self._data_type = DataType.DICT
        elif key == DataType.LIST.value:
            self._data_type = DataType.LIST
        elif key == DataType.TEXT.value:
            self._data_type = DataType.TEXT
        elif key == DataType.BINARY.value:
            self._data_type = DataType.BINARY
        elif key == DataType.ERROR.value:
            self._data_type = DataType.ERROR
        else:
            self._data_type = DataType.DICT

    def parse(self) -> JsonObject:
        """
        Parse the uuDict into a JsonObject.
        """
        return JsonObject(self)

    def save(self, filename: str, encoding: str = 'utf-8'):
        """
        Save the uuDict to a JSON file.
        """
        save_json(self, filename, encoding=encoding)

    @property
    def indentation(self) -> int:
        """
        Get the current indentation level. Default level is 0.
        """
        return self._indentation
    
    @indentation.setter    
    def indentation(self, value: int):
        """
        Set the current indentation level. Default level is 0.
        """
        if not isinstance(value, int):
            raise Exception(f'Indentation must be integer but it is {str(type(value))}')
        if value < 0:
            raise Exception(f'Indentation cannot be negative but it is {value}')
        self._indentation = value

    @property
    def data_type(self) -> DataType:
        """
        Get the data type of the uuDict.
        """
        return self._data_type
    
    @property
    def binary(self) -> bytes | None:
        return self._binary

    def duplicate(self) -> 'uuDict':
        """
        Creates a duplicate copy of the uuDict.
        """
        value = json.dumps(self)
        value = json.loads(value)
        return uuDict(value)

    def case_insensitive_get_key(self, key: str) -> str | None:
        """
        Finds key in dictionary in case insensitive way
        :param key: key to find
        :return: found key or None
        """
        for k in self.keys():
            if k.lower() == key.lower():
                return k
        return None
    
    def case_insensitive_get_value(self, key: str) -> object | None:
        """
        Gets value from dictionary in case insensitive way
        :param key: key to find
        :return: found value or None
        """
        for k in self.keys():
            if k.lower() == key.lower():
                return self[k]
        return None
    
    def case_insensitive_update(self, other: dict):
        """
        Updates dictionary with another dictionary in case insensitive way
        :param other: dictionary to update from
        :return: None
        """
        for k, v in other.items():
            found_key = self.case_insensitive_get_key(k)
            if found_key is not None:
                self[found_key] = v
            else:
                self[k] = v

    def _to_string(self, indentation: int = 4, nested_level: int = 0, end_with_new_line: bool = False,
                  json_like_output: bool = False, force_convert_to_str: bool =False) -> str:
        """
        Converts the uuDict to a string representation.
        """
        if indentation <= 0:
            return str(dict(self))
        indent_end = " " * indentation * nested_level
        indent = " " * indentation * (nested_level + 1)
        result_lines = []
        for k, v in self.items():
            # Handle JsonObject
            if isinstance(v, JsonObject):
                result_lines.append(f"{indent}\"{k}\": {v._to_string(indentation, nested_level + 1)}")
            # Handle ListX
            elif isinstance(v, ListX):
                result_lines.append(f'{indent}"{k}": ' + v._to_string(indentation, nested_level + 1,end_with_new_line=False,
                                                                       json_like_output=json_like_output, force_convert_to_str=force_convert_to_str))
            # Handle list
            elif isinstance(v, list):
                result_lines.append(f'{indent}"{k}": ' + ListX(v)._to_string(indentation, nested_level + 1, end_with_new_line=False,
                                                                            json_like_output=json_like_output, force_convert_to_str=force_convert_to_str))
            # Handle uuDict
            elif isinstance(v, uuDict):
                result_lines.append(f'{indent}"{k}": ' + v._to_string(indentation, nested_level + 1, end_with_new_line=False,
                                                                     json_like_output=json_like_output, force_convert_to_str=force_convert_to_str))
            # Handle dict
            elif isinstance(v, dict):
                result_lines.append(f'{indent}"{k}": ' + uuDict(v)._to_string(indentation, nested_level + 1, end_with_new_line=False,
                                                                             json_like_output=json_like_output, force_convert_to_str=force_convert_to_str))
            # Handle str
            elif isinstance(v, str):
                result_lines.append(f'{indent}"{k}": "{str(v)}"')
            # Handle bool
            elif isinstance(v, bool):
                if json_like_output and force_convert_to_str:
                    result_lines.append(f'{indent}"{k}": "{str(v).lower()}"')
                elif json_like_output and not force_convert_to_str:
                    result_lines.append(f'{indent}"{k}": {str(v).lower()}')
                elif not json_like_output and force_convert_to_str:
                    result_lines.append(f'{indent}"{k}": "{str(v)}"')
                else:
                    result_lines.append(f'{indent}"{k}": {str(v)}')
            # Handle None
            elif v is None:
                if json_like_output and force_convert_to_str:
                    result_lines.append(f'{indent}"{k}": "null"')
                elif json_like_output and not force_convert_to_str:
                    result_lines.append(f'{indent}"{k}": null')
                elif not json_like_output and force_convert_to_str:
                    result_lines.append(f'{indent}"{k}": "None"')
                else:
                    result_lines.append(f'{indent}"{k}": None')
            # Handle other types
            else:
                if force_convert_to_str:
                    result_lines.append(f'{indent}"{k}": "{str(v)}"')
                else:
                    result_lines.append(f'{indent}"{k}": {str(v)}')
        result = f""
        for i, line in enumerate(result_lines):
            result += line + (",\n" if i < len(result_lines) - 1 else "\n")
        if len(result_lines) == 0:
            result = f"{{}}"
        else:
            result = f"{{\n{result}{indent_end}}}"
        if end_with_new_line:
            result += "\n"
        return result
    
    def to_json_str(self, stringify: bool = False):
        """
        Convert the uuDict to a JSON string representation.
        """
        result = self._to_string(indentation=self._indentation, json_like_output=True, force_convert_to_str=stringify)
        return result
    
    def to_str(self, stringify: bool = False):
        """
        Convert the uuDict to a string representation.
        """
        result = self._to_string(indentation=self._indentation, json_like_output=False, force_convert_to_str=stringify)
        return result

    def __str__(self):
        """
        Convert the uuDict to a string representation.
        """
        return self._to_string(indentation=self._indentation)


class ListX(list):
    def __init__(self, *args):
        """
        Initialize the ListX instance.
        """
        super(ListX, self).__init__(*args)
        self._indentation = 0
        for i in range(len(self)):
            if isinstance(self[i], dict):
                self[i] = uuDict(self[i])
            if isinstance(self[i], list):
                self[i] = ListX(self[i])

    @property
    def indentation(self) -> int:
        """
        Get the current indentation level. Default level is 0.
        """
        return self._indentation

    @indentation.setter
    def indentation(self, value: int):
        """
        Set the current indentation level. Default level is 0.
        """
        if not isinstance(value, int):
            raise Exception(f'Indentation must be integer but it is {str(type(value))}')
        if value < 0:
            raise Exception(f'Indentation cannot be negative but it is {value}')
        self._indentation = value

    def parse(self) -> list:
        """
        Parse the ListX into a list of JsonObject.
        """
        result = []
        for item in self:
            if isinstance(item, JsonObject):
                result.append(item)
            elif isinstance(item, ListX):
                result.append(item.parse())
            elif isinstance(item, list):
                result.append(ListX(item).parse())
            elif isinstance(item, uuDict):
                result.append(item.parse())
            elif isinstance(item, dict):
                result.append(uuDict(item).parse())
            else:
                result.append(item)
        return result

    def _to_string(self, indentation: int = 4, nested_level: int = 0, end_with_new_line: bool = False,
                  json_like_output: bool = False, force_convert_to_str: bool =False) -> str:
        """
        Convert the ListX to a string representation.
        """
        if indentation <= 0:
            return str(list(self))
        indent_end = " " * indentation * nested_level
        indent = " " * indentation * (nested_level + 1)
        result_lines = []
        for item in self:
            # Handle JsonObject
            if isinstance(item, JsonObject):
                result_lines.append(item._to_string(indentation, nested_level + 1))
            # Handle ListX
            elif isinstance(item, ListX):
                result_lines.append(indent + item._to_string(indentation, nested_level + 1, end_with_new_line=False,
                                                            json_like_output=json_like_output, force_convert_to_str=force_convert_to_str))
            # Handle list
            elif isinstance(item, list):
                result_lines.append(indent + ListX(item)._to_string(indentation, nested_level + 1, end_with_new_line=False,
                                                                   json_like_output=json_like_output, force_convert_to_str=force_convert_to_str))
            # Handle uuDict
            elif isinstance(item, uuDict):
                result_lines.append(indent + item._to_string(indentation, nested_level + 1, end_with_new_line=False,
                                                            json_like_output=json_like_output, force_convert_to_str=force_convert_to_str))
            # Handle dict
            elif isinstance(item, dict):
                result_lines.append(indent + uuDict(item)._to_string(indentation, nested_level + 1, end_with_new_line=False,
                                                                    json_like_output=json_like_output, force_convert_to_str=force_convert_to_str))
            # Handle str
            elif isinstance(item, str):
                result_lines.append(indent + f'"{item}"')
            # Handle bool
            elif isinstance(item, bool):
                if json_like_output and force_convert_to_str:
                    result_lines.append(indent + f'"{str(item).lower()}"')
                elif json_like_output and not force_convert_to_str:
                    result_lines.append(indent + str(item).lower())
                elif not json_like_output and force_convert_to_str:
                    result_lines.append(indent + f'"{str(item)}"')
                else:
                    result_lines.append(indent + str(item))
            # Handle None
            elif item is None:
                if json_like_output and force_convert_to_str:
                    result_lines.append(indent + f'"null"')
                elif json_like_output and not force_convert_to_str:
                    result_lines.append(indent + "null")
                elif not json_like_output and force_convert_to_str:
                    result_lines.append(indent + f'"None"')
                else:
                    result_lines.append(indent + 'None')
            # Handle other types
            else:
                if force_convert_to_str:
                    result_lines.append(indent + f'"{str(item)}"')
                else:
                    result_lines.append(indent + str(item))
        result = f""
        for i, line in enumerate(result_lines):
            result += line + (",\n" if i < len(result_lines) - 1 else "\n")
        if len(result_lines) == 0:
            result = f"[]"
        else:
            result = f"[\n{result}{indent_end}]"
        if end_with_new_line:
            result += "\n"
        return result

    def to_json_str(self, stringify: bool = False):
        """
        Convert the uuDict to a JSON string representation.
        """
        result = self._to_string(indentation=self._indentation, json_like_output=True, force_convert_to_str=stringify)
        return result

    def to_str(self, stringify: bool = False):
        """
        Convert the uuDict to a string representation.
        """
        result = self._to_string(indentation=self._indentation, json_like_output=False, force_convert_to_str=stringify)
        return result

    def __str__(self) -> str:
        return self._to_string(indentation=self._indentation)
    

def error_message(message: str) -> uuDict:
    """
    Create an error message.
    """
    return uuDict({DataType.ERROR.value: message})


def repeat_letter(value: str = "", letter: str = "#"):
    """
    Repeat a letter to create a border around the value.
    """
    delta = len(value) % 2
    half_len_of_value = math.floor(len(value) / 2)
    result_left_len = 32 - half_len_of_value - delta
    result_right_len = 32 - half_len_of_value
    result = ""
    result += letter * result_left_len
    result += f'{value}'
    result += letter * result_right_len
    return "# " + result + "\n"


def shorten_text(value: str | None,
                 max_lines_from_beginning: int | None = None, max_letters_from_beginning: int | None = None,
                 max_lines_to_end: int | None = None, max_letters_to_end: int | None = None) -> str | None:
    """
    Shortens text if it is too long. It keeps specified number of lines and letters from the beginning
    and specified number of lines and letters from the end of the text. The middle part is replaced by "..."
    :param value: text to be shortened
    :param max_lines_from_beginning: maximum number of lines to keep from the beginning. Default is 25
    :param max_letters_from_beginning: maximum number of letters to keep from the beginning. Default is 700
    :param max_lines_to_end: maximum number of lines to keep from the end. Default is 15
    :param max_letters_to_end: maximum number of letters to keep from the end. Default is 300
    :return: shortened text
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise Exception(f'Parameter "value" must be a string in shorten_text function but it is type of "{str(type(value))}"')
    # setup default values
    max_lines_b = max_lines_from_beginning if max_lines_from_beginning is not None else 25
    max_letters_b = max_letters_from_beginning if max_letters_from_beginning is not None else 700
    max_lines_e = max_lines_to_end if max_lines_to_end is not None else 15
    max_letters_e = max_letters_to_end if max_letters_to_end is not None else 300
    # split lines into array
    lines = value.split("\n")
    len_lines = len(lines)
    # if there is no need to shorten the text then return the original value
    if len_lines <= max_lines_b + max_lines_e and len(value) <= max_letters_b + max_letters_e:
        return value
    # get text from the beginning
    result_b = ""
    total_letters_b = 0
    # will stop after the specified amount of lines
    lines_b = lines[:min(max_lines_b, len_lines)]
    for line in lines_b:
        len_line = len(line)
        # will stop after the specified amount of letters
        if total_letters_b + len_line > max_letters_b:
            result_b += line[:max_letters_b - total_letters_b]
            result_b += "\n"
            break
        # add line
        total_letters_b += len_line
        result_b += line + "\n"
    # get text from the end
    result_e = ""
    total_letters_e = 0
    # will stop after the specified amount of lines
    lines_e = lines[max(0, len_lines - max_lines_e):]
    for line in reversed(lines_e):
        len_line = len(line)
        # will stop after the specified amount of letters
        if total_letters_e + len_line > max_letters_e:
            result_e = line[-(max_letters_e - total_letters_e):] + "\n" + result_e
            # determine indentation of the last line
            line_len = len(line)
            spaces_from_the_beginning = line_len - len(line.lstrip())
            result_e = " " * spaces_from_the_beginning + result_e
            break
        # add line
        total_letters_e += len_line
        result_e = line + "\n" + result_e
    # combine beginning, separator and end and return the result
    separator = "|   " * 16
    result = result_b + separator + "\n" + result_e
    return result


def _safe_str_to_dict(value: str, encoding: str = 'utf-8') -> uuDict:
    """
    Converts str to dict. First tries to convert str to json.
    If it fails it returns dict with plain text
    :param value:
    :return:
    """
    try:
        result = json.loads(value)
        # if result is instance of list
        # replaces list with object containing itemList
        # ["item1", "item2] is replace by {"itemList": ["item1", "item2]}
        if isinstance(result, list):
            result = uuDict({__itemList__: result})
        # result is dict
        else:
            result = uuDict(result)
        return result
    except:
        return uuDict({DataType.TEXT.value: value})


def _safe_bytes_to_dict(value: bytes, encoding: str = 'utf-8') -> uuDict:
    """
    Converts bytes to dict. First tries to convert bytes to json.
    If it fails it tries to convert bytes to string.
    If it fails it tries to convert bytes to base64.
    :param value:
    :param encoding:
    :return:
    """
    try:
        result = value.decode(encoding=encoding)
        return _safe_str_to_dict(result)
    except:
        return uuDict({DataType.BINARY.value: base64.b64encode(value).decode()})


def convert_to_str(value: HttpBody, dict_indent: int = 0) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if dict_indent > 0:
            return json.dumps(value, indent=dict_indent, ensure_ascii=False)
        return json.dumps(value)
    raise Exception("Unexpected type of value. Value must be either dict or json or str")


def safe_convert_to_str(value: HttpBody, dict_indent: int = 0) -> str:
    result = convert_to_str(value, dict_indent=dict_indent)
    if result is None:
        return ""
    return result


def escape_text(value: str) -> str:
    """
    Escapes text in error message
    :param value:
    :return:
    """
    result = ""
    allowed_letters = '0123456789/*-+.,<>?`´\'"~!@#$%^&*()_-=[]{}:\\|abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ \t\n\r'
    result = ''
    for letter in value:
        if letter in allowed_letters:
            result += letter
        else:
            result += "~"
    return result


def timestamp() -> str:
    """
    Returns current local time in ISO format with UTC offset
    :return: string like "[2023-11-02T15:04:05 local, +02H utc]"    
    """
    local_time = datetime.datetime.now()
    utc_time = datetime.datetime.utcnow()
    delta = int(round((local_time-utc_time).seconds / 3600, 0))
    local_time = datetime.datetime(local_time.year, local_time.month, local_time.day,
                                   local_time.hour, local_time.minute, local_time.second)
    result = f"[{local_time.isoformat()} local, +{delta:02}H utc]"
    return result



def linearize_dictionary(dictionary: dict, parent_path: str = "") -> dict:
    """
    From dict structure of {"level1": {"level2": {"variable1": "value1", "variable2": "value2"}}} creates dictionary
    {"level1.level2.variable1": "value1", "level1.level2.variable2": "value2"}
    :param dictionary:
    :param parent_path:
    :return:
    """
    result = {}
    for key, value in dictionary.items():
        if isinstance(value, str) or isinstance(value, int):
            result.update({f'{parent_path}{key}': value})
        else:
            sub_dictionary = linearize_dictionary(value, f'{parent_path}{key}.')
            for skey, svalue in sub_dictionary.items():
                result.update({skey: svalue})
    return result


def dict_path_exists(item: dict, path: str, is_null_value_allowed: bool = True) -> bool:
    """
    Test if dictionary contains specific path. For example if html is written like a JSON
    the user can test if json contains element h1 like this dict_path_exists(json, "html.body.h1")
    :param item:
    :param path:
    :param is_null_value_allowed:
    :return:
    """
    stop_pos = path.find(f'.')
    # if this is the last element and there are no more dots
    # then test if the element is not None (if required) and return True
    if stop_pos < 0:
        if path in item.keys():
            if is_null_value_allowed:
                return True
            else:
                return item[path] is not None
        return path in item.keys()
    # if this is not the last element
    else:
        key = path[:stop_pos]
        remaining_path = path[stop_pos+1:]
        if key not in item.keys():
            return False
        else:
            return dict_path_exists(item[key], remaining_path)


def dict_multiple_path_exists(item: dict, paths: List[str], is_null_value_allowed: bool = True) -> bool:
    """
    Test if dictionary contains multiple paths. If all paths exists the result value is True.
    Otherwise the result value is False.
    :param item:
    :param paths:
    :param is_null_value_allowed:
    :return:
    """
    for path in paths:
        if not dict_path_exists(item, path, is_null_value_allowed):
            return False
    return True


def dict_get_item_by_path(item: dict, path: str) -> dict | object:
    """
    Gets item from dictionary by path. For example if html is written like a JSON
    the user can get element h1 like this dict_get_item_by_path(json, "html.body.h1")
    :param item: dictionary
    :param path: path to the item separated by dots (e.g. "html.body.h1")
    :return: item at the specified path or None if the path does not exist
    """
    stop_pos = path.find(f'.')
    if stop_pos < 0:
        if path not in item.keys():
            raise Exception(f'Item does not exist at path "{path}" in given ditionary.')
        return item[path]
    else:
        key = path[:stop_pos]
        remaining_path = path[stop_pos+1:]
        if key not in item.keys():
            return None
        else:
            return dict_get_item_by_path(item[key], remaining_path)


def substitute_variables(value: str, variables_dict: dict, var_begin: str = "${", var_end: str = "}") -> str:
    """
    Substitutes variables in template string with variable from dictionary
    For example if value is "Hello ${name} ${surname}" and variables_dict is {"name": "John", "surname": "Smith"}
    the result will be "Hello John Smith"
    :param value:
    :param variables_dict:
    :param var_begin:
    :param var_end:
    :return:
    """
    if not isinstance(value, str):
        return value
    result = ""
    remaining = value
    len_begin = len(var_begin)
    len_end = len(var_end)
    pos_begin = value.find(var_begin)
    while pos_begin >= 0:
        result += remaining[:pos_begin]
        remaining = remaining[pos_begin + len_begin:]
        pos_end = remaining.find(var_end)
        if pos_end <= 0:
            raise Exception(f"Cannot find \"{var_end}\" in string: {remaining}")
        variable_name = remaining[:pos_end]
        if variable_name not in variables_dict.keys():
            raise Exception(f'Variable with name "{variable_name}" in string "{value}" cannot be substituted because it  is not in dictionary {variables_dict}')
        result += variables_dict[variable_name]
        remaining = remaining[pos_end + len_end:]
        pos_begin = remaining.find(var_begin)
    result += remaining
    return result