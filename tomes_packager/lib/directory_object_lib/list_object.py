#!/usr/bin/env python3

""" This module contains a class for providing list-like methods for accessing information 
about files and folders. """

# import modules.
import logging
import logging.config
import re

    
class ListObject(list):
    """ A class for providing list-like methods for accessing information about files and
    folders. """


    def __init__(self):
        """ Sets instance attributes. """

        # set logger; suppress logging by default.
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())


    def __getattr__(self, attr):
        """ Adds dynamic support for custom attributes. """
        
        # dynamically support custom attributes.
        if attr == "names":
            return self._get_names()
        if attr == "basenames":
            return self._get_names(basenames=True)


    @classmethod
    def _this(cls, *args, **kwargs):
        """ Returns instance of this class. """

        return cls(*args, **kwargs)


    def _get_names(self, indices=None, basenames=False):
        """ Returns a list of names for each file or folder in @self if @indicies is None.
        Otherwise, only the list of names for each item index in @indices.
        
        Args:
            - indices (list): A list of integers, with each integer corresponding to and 
            item's index in @self.
            - basenames (bool): If True, returns only the basenames of the file or folder.
            Otherwise, returned the relative name.

        Returns:
            list: The return values.
        """
        
        # if @indices is None, build it.
        if indices == None:
            indices = range(0, len(self) + 1)
        
        # create a list of name attributes for each required item.
        if basenames:
            names = [s.name for s in self if self.index(s) in indices]
        else:
            names = [s.name for s in self if self.index(s) in indices]
        return names


    def find(self, name):
        """ Returns the index of @name in @self. If @name is not in @self, None will be 
        returned.
        
        Args:
            - name (str): The name of the file or folder to look for.
            
        Returns:
            int: The return value.
        """

        # assume @name is not in @self.
        index = None

        # search for @name in @self.
        for s in self:
            if s.name == name:
                index = self.index(s)
                break
        
        return index

        
    def search(self, term):
        """ Returns a list of indexes in @self for every successful search for @term. 
        
        Args:
            - term (str): The term to search for in @self. 
            
        Returns:
            list: The return value.
        """

        # container.
        results = []
        
        # for each regex match on @term, append the index of match in @results.
        for s in self:

            try:
                match = re.search(term, s.name)
            except re.error as err:
                self.logger.warning("Search term '{}' is invalid; aborting search.".format(
                    term))
                self.logger.error(err)
                return
            
            # append index of match to @results.
            if match is not None:
                results.append(self.index(s))
        
        return results


    def sort(self):
        """ Sorts file or folder objects alphabetically.
        
        Returns:
            ListObject: The return value.
        """

        # create container ListObject instance. 
        resorted = self._this()
        
        # sorted @self. 
        for s in sorted(self._get_names()):
            item = self.find(s)
            item = self[item]
            resorted.append(item)
        
        return resorted


    def ls(self):
        """ Returns a string representation of the file or folder object.

        Returns:
            str: The return value.
        """
        
        # if @self is a folder, sort it.
        if len(self) > 0 and self[0].isdir:
            self = self.sort()

        # create container string.
        viz = ""
        if self[0].isdir:
            viz = self[0].parent_object.name + "\n"
        
        # for each item in @self, add strings to @viz. 
        for s in self:

            # add folders and their files.
            if s.isdir:
                viz += "{}{}/\n".format(" " * s.depth, s.basename)
                for fil in s.files:
                    viz += "{}{}\n".format("  " * s.depth, fil.basename)
            
            # add root level files.
            else:
                viz += "{}\n".format(s.name)
        
        return viz


if __name__ == "__main__":
    pass