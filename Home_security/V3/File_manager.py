import os
import shutil



class FileManager(object):

    def __init__(self, work_directory):
        self.file_path = os.path.abspath(__file__)
        self.file_directory = os.path.dirname(self.file_path)
        self.file_dicts = {}
        self.program_directory = ""
        self.work_directory = self.file_directory 
        self.set_work_directory('program_files')
        self.set_work_directory(work_directory) 
        
    #set work directory to not affect any other programs which might be using directoty
    def set_work_directory(self, path):
        self.work_directory = self.create_path(path)
        if not self.folder_exists(self.work_directory, path):
            self.create_dir(self.work_directory)
        if not self.folder_exists(self.work_directory, path):
            print('[File_Manager]: failed to start File Manager')
            raise

    #create paths
    def create_path(self, path):
        full_path =self.work_directory
        if not type(path) is list:
            path = [path]
        for p in path:
            full_path = os.path.join(full_path, p)
        return full_path

    #create folder
    def create_dir(self, path):
        os.makedirs(path)

    def folder_exists(self, path, key, return_bool=False):
        if(os.path.exists(path)):
            self.file_dicts[key] = path
            return True
        if return_bool:
            return os.path.exists(path)
    
    #create folder and assign key
    def folder_handler(self, path, key, return_bool=True):
        full_path = self.create_path(path)
        self.folder_exists(full_path, key)
        if key not in self.file_dicts:
            self.create_dir(full_path)
            self.folder_exists(full_path, key)
        if return_bool:
            if key in self.file_dicts:
                return True
            else:
                return False

    
    def folder_handler_multiple(self, paths, keys ,return_list=True):
        created_list = []
        for path, key in zip(paths, keys):
            if not type(path) is list:
                path = [path]
            created_list.append(self.folder_handler(path, key))

        if return_list:
            return created_list

    #get created folder
    def get_folder(self, key):
        if key in self.file_dicts:
            return self.file_dicts[key]
        else:
            return False
        
    #remove existing folder based on key
    def remove_folder_key(self, key):
        if key in self.file_dicts:
            shutil.rmtree(self.get_folder(key))    
        del self.file_dicts[key]
    
    #remove the folder based on path
    def remove_folder_path(self, path):
        full_path = self.create_path(path)
        if self.folder_exists(full_path, full_path, return_bool=True):
            self.remove_folder_key(full_path)
    
    #remove everything in a folder
    def deep_clean_folder(self, key):
        temp = self.get_folder(key)
        self.remove_folder_key(key)
        self.folder_handler(temp, key, return_bool=False)
    
    #remove only files in a folder
    def clean_folder(self, key):
        full_path = self.get_folder(key)
        
        files = [os.path.join(full_path ,f) for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path ,f))]
        if not type(files) is list:
            files = [files]
        for file in files:
            os.remove(file)
                
    def return_file_dict(self):
        print(self.file_dicts)
    
        
if __name__ == '__main__':
    fm = FileManager('test2')
    print(fm.folder_handler_multiple([['program_files', 'fuck you'],['test', '2'],'double'], [1,2,3]))
    # print(fm.return_file_dict())