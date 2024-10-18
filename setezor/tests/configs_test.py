import json
import os
import uuid
import tempfile
import pytest
import hashlib
import orjson
from io import BytesIO
from pydantic import BaseModel
from setezor.tools.ip_tools import get_interfaces, get_default_interface
from setezor.exceptions.loggers import get_logger
from setezor.network_structures import AgentStruct
from setezor.modules.project_manager.files import FilesStructure
from setezor.modules.project_manager.configs import Configs, Files, Folders, Variables, SchedulersParams, FilesNames


class TestGenerateConfigs:
    
    @pytest.fixture
    def setup(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            project_path = tmpdirname
            project_name = str(uuid.uuid4())
            yield project_path, project_name
    
    def test_generate_configs_creates_instance(self, setup):
        project_path, project_name = setup
        config_instance = Configs.generate_configs(project_path, project_name)
    
        """ Проверка, что экземпляр был создан и имеет правильные значения """

        assert isinstance(config_instance, Configs)
        assert config_instance.variables.project_name == project_name

    def test_generate_configs_creates_unique_id(self, setup):
        project_path, project_name = setup
        config_instance = Configs.generate_configs(project_path, project_name)

        """ Проверка, что project_id уникален и соответствует формату UUID """

        assert config_instance.variables.project_id != ""
        try:
            uuid_obj = uuid.uuid4()
        except ValueError:
            pytest.fail("UUID format is invalid")

    def test_generate_configs_folders(self, setup):
        project_path, project_name = setup
        config_instance = Configs.generate_configs(project_path, project_name)

        """ Проверка, что папки были правильно инициализированы """

        assert config_instance.folders.nmap_logs == os.path.join(os.path.abspath(project_path), config_instance.variables.project_id, 'nmap_logs')
        assert config_instance.folders.scapy_logs == os.path.join(os.path.abspath(project_path), config_instance.variables.project_id, 'scapy_logs')
        assert config_instance.folders.screenshots == os.path.join(os.path.abspath(project_path), config_instance.variables.project_id, 'screenshots')
        assert config_instance.folders.masscan_logs == os.path.join(os.path.abspath(project_path), config_instance.variables.project_id, 'masscan_logs')
        assert config_instance.folders.certificates_folder == os.path.join(os.path.abspath(project_path), config_instance.variables.project_id, 'certificates')

    def test_generate_configs_files(self, setup):
        project_path, project_name = setup
        config_instance = Configs.generate_configs(project_path, project_name)

        """ Проверка правильности имен файлов """

        assert config_instance.files.database_file.split('/')[-1] == FilesNames.database_file
        assert config_instance.files.project_configs.split('/')[-1] == FilesNames.config_file
        assert config_instance.files.acunetix_configs.split('/')[-1] == FilesNames.acunetix_configs
 
    def test_save_config_file_creates_files(self, setup, config_file_name: str = FilesNames.config_file):
        project_path, project_name = setup
        config_instance = Configs.generate_configs(project_path, project_name)    

        """ Проверка что файл project_configs.json создается правильно и имеет формат json"""

        files = FilesStructure(folders=config_instance.folders, files=config_instance.files)
        files.create_project_structure()
        
        config_file_path = config_instance.files.project_configs
        config_instance.save_config_file() 

        assert os.path.exists(config_file_path)
        assert config_file_path.endswith('.json')

        try:
            with open(config_file_path, 'r') as json_file:
                json_content = json.load(json_file)
                assert isinstance(json_content, dict)
        except json.JSONDecodeError:
            pytest.fail(f"Config file {config_file_path} is not a valid JSON.")


    def test_load_config_from_file(self, setup):
        
        """ С помощью hashlib проверяю, что project_configs.json до загрузки и после загрузки - одинаковые файлы """

        project_path, project_name = setup
        config_instance = Configs.generate_configs(project_path, project_name)
        config_file_path = config_instance.files.project_configs
        files = FilesStructure(folders=config_instance.folders, files=config_instance.files)
        files.create_project_structure()
        config_instance.save_config_file()

        config_file_hash_before_load = hashlib.sha256()
        with open(config_file_path, 'rb') as f:
           for byte_block in iter(lambda: f.read(4096), b""):
               config_file_hash_before_load.update(byte_block)

        config_file_hash_before_load = config_file_hash_before_load.hexdigest()

        Configs.load_config_from_file(config_instance.project_path)
        
        configs = Configs.get_config_dict(config_instance)
        data = orjson.dumps(configs,
                            default=lambda x: x.model_dump() if isinstance(x, BaseModel) else x.__dict__,
                            option=orjson.OPT_INDENT_2)
        
        config_file_hash_after_load = hashlib.sha256(data).hexdigest()

        assert config_file_hash_after_load == config_file_hash_before_load

        
    def test_delete_key_in_config(self, setup):

        """ Проверка на то, что если удалить в project_configs.json какой-то ключ - он не запустится """

        project_path, project_name = setup
        config_instance = Configs.generate_configs(project_path, project_name)
        config_file_path = config_instance.files.project_configs
        files = FilesStructure(folders=config_instance.folders, files=config_instance.files)
        files.create_project_structure()
        config_instance.save_config_file()
    
        with open(config_file_path, 'r') as f:
            data = json.load(f)

        if "variables" in data:
            del data["variables"]

        with open(config_file_path, 'w') as f:
            json.dump(data, f, indent=4)

        print(json.dumps(data, indent=4))
        with pytest.raises(KeyError):
            Configs.load_config_from_file(config_instance.project_path)

    def test_delete_value_in_config(self, setup):
        
        """ Проверка на то, что если удалить в project_configs.json лишние значения - он не запустится """

        project_path, project_name = setup
        config_instance = Configs.generate_configs(project_path, project_name)
        config_file_path = config_instance.files.project_configs
        files = FilesStructure(folders=config_instance.folders, files=config_instance.files)
        files.create_project_structure()
        config_instance.save_config_file()

        with open(config_file_path, 'r') as f:
            data = json.load(f)

        if "schedulersparams" in data and "nmap" in data["schedulersparams"]:
            if "limit" in data["schedulersparams"]["nmap"]:
                del data["schedulersparams"]["nmap"]["limit"]

        with open(config_file_path, 'w') as f:
            json.dump(data, f, indent=4)

        print(json.dumps(data, indent=4))
        with pytest.raises(TypeError) as excinfo:
            Configs.load_config_from_file(config_instance.project_path)

        assert "SchedulersParams.add() missing 1 required positional argument: 'limit'" in str(excinfo.value)

    def test_add_unnecessery_value_in_config(self, setup):
        
        """ Проверка на то, что если добавить в project_configs.json лишние значения - он не запустится """

        project_path, project_name = setup
        config_instance = Configs.generate_configs(project_path, project_name)
        config_file_path = config_instance.files.project_configs
        files = FilesStructure(folders=config_instance.folders, files=config_instance.files)
        files.create_project_structure()
        config_instance.save_config_file()

        with open(config_file_path, 'r') as f:
            data = json.load(f)

        if "schedulersparams" in data and "nmap" in data["schedulersparams"]:
            if "unnecessary_value" not in data["schedulersparams"]["nmap"]:
                data["schedulersparams"]["nmap"]["unnecessary_value"] = 1000 

        with open(config_file_path, 'w') as f:
            json.dump(data, f, indent=4)

        print(json.dumps(data, indent=4))
        with pytest.raises(TypeError) as excinfo:
            Configs.load_config_from_file(config_instance.project_path)

        assert "unexpected keyword argument 'unnecessary_value'" in str(excinfo.value)
