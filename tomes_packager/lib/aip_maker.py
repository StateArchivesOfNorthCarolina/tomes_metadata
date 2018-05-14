#!/usr/bin/env python3

""" This module contains a class for constructing the basic file and folder structure for a 
TOMES archival information package (AIP). """

# import modules.
import glob
import logging
import logging.config
import os
import shutil


class AIPMaker():
    """ A class for constructing the basic file and folder structure for a TOMES archival 
    information package (AIP).
    
    Attributes:
        - root (str): The root path of the created AIP structure.
        - pst_dir (str): = The optional "/pst" folder path within the AIP or None if empty 
        after self.make().
        - mime_dir (str): The required "/mime" folder path within the AIP or None if empty 
        after self.make().
        - eaxs_dir (str): The required "/eaxs" folder within the AIP or None if empty after 
        self.make().
        - metadata_dir (str): The optional "/metadata" folder within the AIP or None if empty 
        after self.make().
        - transfers (dict): The log of file transfers with keys: "attempted", "passed", and
        "failed". Each key's value is a list.

    Example:
        >>> sample_dir = "../../tests/sample_files/"
        >>> aip = AIPMaker("foo", sample_dir + "/hot_folder", sample_dir)
        >>> aip.make() # returns path to the new "foo" AIP folder.
        >>> aip.validate() # True
    """

    
    def __init__(self, account_id, source_dir, destination_dir):
        """ Sets instance attributes.

        Args:
            - account_id (str): The email account's base identifier, i.e. the file prefix.
            - source_dir (str): The folder path from which to transfer data.
            - destination_dir (str): The folder path in which to create the AIP structure.

        Raises:
            - NotADirectoryError: If @source_dir or @destination_dir are not actual folder 
            paths.
        """

        # set logger; suppress logging by default.
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())

        # verify source_dir and destination_dir are folders.
        if not os.path.isdir(source_dir):
            msg = "Can't find source: {}".format(source_dir)
            self.logger.error(msg)
            raise NotADirectoryError(msg)
        if not os.path.isdir(destination_dir):
            msg = "Can't find destination: {}".format(destination_dir)
            self.logger.error(msg)
            raise NotADirectoryError(msg)

        # set attributes.
        self.account_id = str(account_id) 
        self.source_dir = source_dir
        self.destination_dir = destination_dir
        
        # convenience functions to join paths and normalize them.
        self._normalize_path = lambda p: os.path.relpath(p).replace("\\", "/")  
        self._join_paths = lambda *p: self._normalize_path(os.path.join(*p))
        
        # set source attributes.
        self._source_pst = self._join_paths(self.source_dir, "pst")
        self._source_mime = self._join_paths(self.source_dir, "mime", self.account_id)
        self._source_eaxs = self._join_paths(self.source_dir, "eaxs", self.account_id)
        self._source_metadata = self._join_paths(self.source_dir, "metadata", self.account_id)

        # set destination attributes.
        self.root = self._join_paths(self.destination_dir, self.account_id)
        self.pst_dir = self._join_paths(self.root, "pst")
        self.metadata_dir = self._join_paths(self.root, "metadata")
        self.mime_dir = self._join_paths(self.root, "mime")
        self.eaxs_dir = self._join_paths(self.root, "eaxs")

        # track data regarding transfer attempts.
        self.transfers = {"attempted": [], "passed": [], "failed": []}


    def _remove_folder(self, folder):
        """ Removes the given @folder if it is empty. 
        
        Args:
            - folder (str): The folder path to remove.
            
        Returns:
            None
        """

        # check if @folder is empty.
        if len(os.listdir(folder)) != 0:
            self.logger.warning("Can't delete non-empty folder: {}".format(folder))
            return
        
        # delete @folder.
        self.logger.info("Deleting folder: {}".format(folder))
        try:
            shutil.rmtree(folder)
        except OSError as err:
            self.logger.warning("Can't delete source folder: {}".format(folder))
            self.logger.error(err)
        
        return


    def _create_folder(self, folder):
        """ Creates a given @folder.

        Args:
            - folder (str): The folder path to create.
        
        Returns:
            None
        
        Raises:
            - OSError: If the folder can't be created.
        """

        # make @folder.
        try:
            self.logger.info("Making folder: {}".format(folder))        
            os.mkdir(folder)
        except OSError as err:
            self.logger.warning("Unable to create folder: {}".format(folder))
            self.logger.error(err)
            raise OSError(err)

        return


    def _transfer_data(self, source_dir, destination_dir, find_files=True):
        """ Moves data in @source_dir to @destination_dir. If @find_files is True, only
        files in @source_dir with basenames that equal @self.account_id will be moved.
        Otherwise, all subfolders (and their files) in @source_dir will be moved.
        
        Args:
            - source_dir (str): The folder path from which to move data.
            - destination_dir (str): The folder path into which to move data.
            - is_files (bool): Use True to move files (as described above). Use False to move
            subfolders.
        
        Returns:
           None
        """
        
        self.logger.info("Looking for candidate data in: {}".format(source_dir))
        
        # verify @source_dir exists.
        if not os.path.isdir(source_dir):
            self.logger.warning("Can't find folder '{}'; skipping.".format(source_dir))
            return

        # per @find_files, determine what data to move.
        if find_files:
            data_glob = glob.glob(source_dir + "/*.*")
            data = [self._normalize_path(f) for f in data_glob
                    if os.path.splitext(os.path.basename(f))[0] == self.account_id]
        else:
            data_glob = glob.glob(source_dir + "/*")
            data = [self._normalize_path(f) for f in data_glob]

        # if @data is empty set the corresponsing folder attribute to None, otherwise store 
        # what data should be moved in @self.transfers.
        if len(data) == 0:
            self.logger.info("Unable to find any candidate data to move.")
            for key in self.__dict__:
                if self.__dict__[key] == destination_dir:
                    self.logger.debug("Setting instance attribute '{}' to None.".format(key))
                    self.__dict__[key] = None
                    break
            return
        else:
            self.transfers["attempted"] += data
            self.logger.info("Moving the following items: {}".format(data))
        
        # if needed, create @destination_dir.
        if not os.path.isdir(destination_dir):  
            self._create_folder(destination_dir)

        # move items in @data.
        for item in data:
            try:
                self.logger.info("Moving '{}' to: {}".format(item, destination_dir))
                shutil.move(item, destination_dir)
                self.transfers["passed"].append(item)
            except OSError as err:
                self.logger.warning("Can't move '{}' to: {}".format(item, destination_dir))
                self.logger.error(err)
                self.transfers["failed"].append(item)

        # if moving an entire tree, remove @source_dir.
        if not find_files:
            self._remove_folder(source_dir)

        return


    def validate(self):
        """ Determine if the AIP structure appears to be valid.

        Returns:
            bool: The return value.
            True if the AIP appears to be valid. Otherwise, False.
        """
    
        self.logger.info("Testing if AIP structure is valid.")

        # if @self.root doesn't exist, the AIP is invalid.
        if not os.path.isdir(self.root):
            self.logger.warning("AIP folder doesn't exist.".format(self.root))
            self.logger.info("Trying running .make() first.")
            return False
        
        # store validation tests.
        validation_tests = []

        # test if all transfer attempts were successful.
        test = self.transfers["attempted"] == self.transfers["passed"]
        validation_tests.append(test)
        if not test:
            self.logger.warning("Not all attempted transfers passed.")
        else:
            self.logger.info("All attempted transfers passed.")

        # test if no transfers failed (theoretically redundant vs. the previous test).
        test = len(self.transfers["failed"]) == 0
        validation_tests.append(test)
        if not test:
            self.logger.warning("Failed transfers: {}".format(self.transfers["failed"]))

        # test if MIME and EAXS folders exists in AIP and aren't empty.
        for required_folder in [self.mime_dir, self.eaxs_dir]:
            
            test = os.path.isdir(required_folder)
            validation_tests.append(test)
            if not test:
                self.logger.warning("Missing required folder: {}".format(required_folder))
                continue
            else:
                self.logger.info("Found required folder: {}".format(required_folder))
            
            test = len(os.listdir(required_folder)) !=0
            validation_tests.append(test)
            if not test:
                self.logger.warning("No data in required folder: {}".format(required_folder))
            else:
                self.logger.info("Found data in required folder: {}".format(required_folder))

        # if False is in @validation_tests; the AIP cannot be valid.
        is_valid = False not in validation_tests

        # report on validity.
        if is_valid:
            self.logger.info("AIP structure appears to be valid.")
        else:
            self.logger.warning("AIP structure appears to invalid.")
         
        return is_valid


    def make(self):
        """ Create the AIP structure.

        Returns:
            str: The return value.
            The path to the AIP structure's root. 

        Raises:
            IsADirectoryError: If @self.root already exists.
        """

        # verify @self.root doesn't already exist.
        if os.path.isdir(self.root):
            msg = "AIP destination '{}' already exists.".format(self.root)
            self.logger.error(msg)
            raise IsADirectoryError(msg)
        else:
            self.logger.info("Creating AIP structure at: {}".format(self.root))

        # create @self.root and move data into it.
        self._create_folder(self.root)        
        self._transfer_data(self._source_pst, self.pst_dir)
        self._transfer_data(self._source_mime, self.mime_dir, False)
        self._transfer_data(self._source_eaxs, self.eaxs_dir, False)
        self._transfer_data(self._source_metadata, self.metadata_dir, False)

        # move stray metadata files in @self.source_dir to @self.metadata_dir.
        self._transfer_data(self.source_dir, self.metadata_dir)

        return self.root


if __name__ == "__main__":
    pass
