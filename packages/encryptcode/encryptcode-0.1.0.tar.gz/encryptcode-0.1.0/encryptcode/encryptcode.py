from cryptography.fernet import Fernet, InvalidToken
from pathlib import Path
from datetime import datetime, date, timezone
import sys, os, re, argparse, base64, random, json


class Encryptcode():

    __seed = None
    __key = None


    def __call__(self, module_name, code):
        self.__encryptcode(module_name, code)


    def __encryptcode(self, module_name, code):
        try:
            if self.__key:
                k = base64.b64encode(bytes.fromhex(self.__key.decode()[self.__seed:self.__seed+self.__key_size]))
                code = Fernet(k).decrypt(code)
                ## Execute the script content in a module
                module = sys.modules.get(module_name)
                exec(code, module.__dict__)
            else:
                raise InvalidToken

        except InvalidToken:
            print("\n\n\t\tERROR IN IMPORTING PACKAGE(s): INVALID TOKEN\n\n")
        except Exception as e:
            err_msg = self.__err_format(sys.exc_info(), '%s.__encryptcode' %module_name)
            print(f"\n\n\t\tERROR IN IMPORTING PACKAGE(s): %s\n\n" %err_msg)
        finally:
            pass
    
    
    def _addkey(self, pyfile):
        try:
            with open(pyfile, 'r') as fh:
                content = fh.read()
            with open(pyfile, 'w') as fh:
                _seed = random.randint(0,self.__random_key_size-self.__key_size)
                _key = self.__gen_key(seed=_seed)
                content = re.sub('(__seed = )None', r'\g<1>%s' %_seed, content)
                content = re.sub('(__key = )None', r'\g<1>%s' %_key, content)
                fh.write(content)
        except Exception as e:
            print(f'ERROR: {e}')


    def __gen_key(self, seed):
        _key = base64.b64decode(base64.b64encode(os.urandom(int(self.__key_size/2)))).hex()
        random_hex = os.urandom(int((self.__random_key_size-self.__key_size)/2)).hex()
        _key = random_hex[0:seed] + _key + random_hex[seed::]
        _key = _key.encode()
        return _key
    
    
    def _encrypt(self, path):
        _format = "from encryptcode.encryptcode import Encryptcode\nEncryptcode()(__name__, b\'{f_content}\')"
        files = self.__find_py_files(path)
        for file in files:
            with open(file, 'rb') as fh:
                k = base64.b64encode(bytes.fromhex(self.__key.decode()[self.__seed:self.__seed+self.__key_size]))
                f_content = Fernet(k).encrypt(fh.read())
            with open(file, 'wb') as fh:
                fh.write(_format.format(f_content=f_content.decode()).encode())
    
    
    def __find_py_files(self, path):
        if os.path.isdir(path):
            return list(Path(path).rglob('*.py'))
        else:
            return [path]
    
    
    def __err_format(self, err, api):
        _type, _obj, _trace = err
        _class = api
        _function = _trace.tb_frame.f_code.co_name
        _api = '%s.%s' % (_class, _function)
        _line = _trace.tb_lineno
        _file = _trace.tb_frame.f_code.co_filename
        err_msg = """
        %s\t\t%s
        ERROR:  Line: %s, API: "%s", File: %s""" % (_type, _obj, _line, _api, _file)
        return err_msg

    __random_key_size = 4096
    __key_size = 64

if __name__ == '__main__':
    en = Encryptcode()
    banner = """
                ┌───────────────────────────────────────────────────────────┐
                │┌─────────────────────────────────────────────────────────┐│
                ││                                                         ││
                ││                       ENCRYPTCODE                       ││
                ││                                                         ││
                ││              A TOOL TO ENCRYPT PYTHON FILES             ││
                ││                                                         ││
                ││  ENCRYPTS PYTHON CODE KEEPING ITS FUNCTIONALITY INTACT  ││
                ││                                                         ││
                │└─────────────────────────────────────────────────────────┘│
                └───────────────────────────────────────────────────────────┘
    """
    print(banner)
    parser = argparse.ArgumentParser(description=""""ENCRYPTCODE": A TOOL TO ENCRYPT PYTHON SCRIPTS""")
    parser.add_argument('-f', '--file', type=str, help=': NAME OF THE PACKAGE FILE WHERE CRYPTOGRAPHY KEY TO BE ADDED, (USED ALONG WITH -k|--addkey FLAG ONLY')
    enc_group = parser.add_argument_group('ENCRYPT PACKAGE', 'ENCRYPT PACKAGE, A FILE OR DIRECTORY, GIVEN UNDER -p or --path OPTION')
    key_group = parser.add_argument_group('ADD KEY', 'ADD CRYPTOGRAPHY KEY TO THE PACKAGE')

    enc_group.add_argument('-e', '--encrypt', action='store_true', help=': FLAG TO ENABLE ENCRYPTION ON GIVEN PATH (USED ONLY WITH -p OR --path)')
    enc_group.add_argument('-p', '--path', type=str, help=': PATH OF THE DIRECTORY OR FILE WHICH NEED TO BE ENCRYPTED (USED ONLY WITH -e OR --encrypt FLAG)')
    key_group.add_argument('-k', '--addkey', action='store_true', help=': FLAG TO ENABLE ADDING DYNAMIC CRYPTOGRAPHY KEY TO THE PACKAGE FILE')

    args = parser.parse_args()
    try:

        # encrypt should not go with addlic or addkey
        if (args.encrypt and args.addkey):
            raise Exception('-e|--encrypt cannot be used with -k|--addkey')

        if args.addkey:
            if args.file:
                en._addkey(pyfile=args.file)
            else:
                raise Exception('-f|--file is required along with -k|--addkey option')

        if args.encrypt:
            if args.path:
                en._encrypt(path=args.path)
            else:
                raise Exception('-p|--path is required along with -e|--encrypt option')

    except Exception as e:
        print(f'\n\n\t\tERROR!!: {e}\n\n')
