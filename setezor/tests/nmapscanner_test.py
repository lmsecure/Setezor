import pytest
import json
import xmltodict
import traceback
from unittest.mock import AsyncMock, MagicMock, patch
from setezor.modules.nmap.scanner import  NmapScanner

def test_parse_xml_with_non_xml_input():

    """ Неверный случай: ввод, не являющийся XML """

    input_xml = "This is not an XML string"
    
    with pytest.raises(Exception, match='Error with parsing nmap xml-file'):
        NmapScanner.parse_xml(input_xml)

def test_parse_xml_with_nested_elements():
    
    """ Успешный случай: XML с вложенными элементами """

    input_xml = '''<nmaprun>
        <host>
            <address addr="192.168.1.1" addrtype="ipv4"/>
            <ports>
                <port protocol="tcp" portid="22">
                    <state state="open"/>
                </port>
                <port protocol="tcp" portid="80">
                    <state state="closed"/>
                </port>
            </ports>
        </host>
    </nmaprun>'''

    expected_result = {
        'nmaprun': {
            'host': {
                'address': {'addr': '192.168.1.1', 'addrtype': 'ipv4'},
                'ports': {
                    'port': [
                        {'protocol': 'tcp', 'portid': '22', 'state': {'state': 'open'}},
                        {'protocol': 'tcp', 'portid': '80', 'state': {'state': 'closed'}}
                    ]
                }
            }
        }
    }

    result = NmapScanner.parse_xml(input_xml)
    assert result == expected_result


def test_parse_xml_missing_closing_tag():

    """ Успешный случай: XML без закрывающего nmaprun, функция должна его добавить """

    input_xml = '''<nmaprun>
        <host>
            <address addr="192.168.1.1" addrtype="ipv4"/>
        </host>'''
    
    expected_result = {
        'nmaprun': {
            'host': {
                'address': {'addr': '192.168.1.1', 'addrtype': 'ipv4'}
            }
        }
    }

    result = NmapScanner.parse_xml(input_xml)
    assert result == expected_result

def test_parse_xml_invalid_xml():

    """ Неверный случай: XML с синтаксической ошибкой, в которой нет закрывающего '/' в адресс """

    input_xml = '''<nmaprun>
        <host>
            <address addr="192.168.1.1" addrtype="ipv4">
        </host>'''
    
    with pytest.raises(Exception, match='Error with parsing nmap xml-file'):
        NmapScanner.parse_xml(input_xml)

class TestCheckResult:
    @pytest.fixture
    def my_class_instance(self):
        instance = NmapScanner()
        instance.save_source_data = MagicMock()
        instance.parse_xml = MagicMock(return_value={'key': 'value'})
        return instance

    def test_check_results_success(self, my_class_instance):

        """ Проверяем, что функция отрабатывает корректно"""

        args = ['nmap', '-sP', '192.168.1.1']
        result = '<results></results>'
        error = ''
        logs_path = 'path/to/logs'

        result_dict = my_class_instance._check_results(args, result, error, logs_path)

        assert result_dict == {"key": "value"}
        my_class_instance.save_source_data.assert_called_once_with(path=logs_path, command=' '.join(args), scan_xml=result)

    def test_check_results_success_with_bytes(self, my_class_instance):

        """ Проверяем, что функция отрабатывает корректно если передать результат в байтах"""

        args = ['nmap', '-sP', '192.168.1.1']
        result = b'<results></results>'
        error = ''
        logs_path = 'path/to/logs'

        result_dict = my_class_instance._check_results(args, result, error, logs_path)

        assert result_dict == {'key': 'value'}
        my_class_instance.save_source_data.assert_called_once_with(path=logs_path, command=' '.join(args), scan_xml=result.decode())

    def test_check_results_sudo_error(self, my_class_instance):

        """ Проверяем, что sudo error в функции отрабатывает корректно"""

        args = ['nmap', '-sP', '192.168.1.1']
        result = '<results></results>'
        error = '[sudo] password for user:'
        logs_path = 'path/to/logs'

        result_dict = my_class_instance._check_results(args, result, error, logs_path)

        assert result_dict == {"key": "value"}
        my_class_instance.save_source_data.assert_called_once_with(path=logs_path, command=' '.join(args), scan_xml=result)

    def test_check_results_other_error(self, my_class_instance):

        """ Проверяем, что если выдается не указанный в функции error, то вылетит ошибка"""

        args = ['nmap', '-sP', '192.168.1.1']
        result = '<results></results>'
        error = 'Ошибочная ошибка, извините'
        logs_path = 'path/to/logs'

        with pytest.raises(Exception) as exc_info:
            my_class_instance._check_results(args, result, error, logs_path)

        assert str(exc_info.value) == error
        my_class_instance.save_source_data.assert_not_called() # Тут проверяем что лог не сохраняется

    def test_check_results_failure_with_bytes_error(self, my_class_instance):

        """ Проверяем, что если передается не указанный в функции error в БАЙТАХ, то тоже вылетит ошибка"""
        
        args = ['nmap', '-sP', '192.168.1.1']
        result = '<results></results>'
        error = b'Nmap failed due to timeout'
        logs_path = 'path/to/logs'
        with pytest.raises(Exception) as exc_info:
            my_class_instance._check_results(args, result, error, logs_path)

        assert str(exc_info.value) == error.decode()
        my_class_instance.save_source_data.assert_not_called() # Тут проверяем что лог не сохраняется


@pytest.fixture
def nmap_scanner():
    return NmapScanner()


def test_run_success(mocker, nmap_scanner):
    """ Проверка успешного запуска run, он проверяет, что результатом будет выдан словарь, также все функции которые вызывает run успешно отработали,
        shell_subprocess тоже вызвался единожды с переданными в нее значениями sudo и аргументами"""

    mock_create_shell_subprocess = mocker.patch('setezor.modules.nmap.scanner.create_shell_subprocess')
    mock_process = MagicMock()
    mock_process.communicate.return_value = (b'<?xml version="1.0"?><nmaprun></nmaprun>', b'') 
    mock_create_shell_subprocess.return_value = mock_process

    extra_args = '-sP 192.168.1.0/24'
    password = 'password'

    mocker.patch.object(nmap_scanner, '_prepare_args', return_value=['nmap'] + [extra_args]) 
    mocker.patch.object(nmap_scanner, '_check_results', return_value={'success': True})

    result = nmap_scanner.run(extra_args, password)

    args_called = mock_create_shell_subprocess.call_args[0][0]
    assert args_called == ['sudo', '-S'] + ['nmap'] + [extra_args] 
    assert 'nmap' in args_called

    assert isinstance(result, dict) 
    assert result == {'success': True}  
    mock_create_shell_subprocess.assert_called_once() 



def test_save_source_data_success(mocker, nmap_scanner):

    """ Проверяем данные успешно сохранились, проверяем правильность пути.

        Также проверям, что функция `open` была вызвана ровно один раз, это подтверждает, что метод пытался открыть файл для записи.
    """

    mock_open = mocker.patch('builtins.open', mocker.mock_open())
    path = '/fake/path'
    scan_xml = '<?xml version="1.0"?><nmaprun></nmaprun>'
    command = 'nmap -sP 192.168.1.0/24'
    
    result = nmap_scanner.save_source_data(path, scan_xml, command)
    
    assert result is True
    mock_open.assert_called_once()
    assert mock_open.call_args[0][0].startswith('/fake/path')  # Проверка пути


def test_save_source_data_failure(mocker, nmap_scanner):

    """ Проверка, что ошибка отрабатывает корректно"""

    mocker.patch('builtins.open', side_effect=OSError("File save error"))

    path = '/fake/path'
    scan_xml = '<?xml version="1.0"?><nmaprun></nmaprun>'
    command = 'nmap -sP 192.168.1.0/24'
    
    with pytest.raises(Exception, match='Failed save source scan to path'):
        nmap_scanner.save_source_data(path, scan_xml, command)


@pytest.mark.asyncio
async def test_async_run_success(mocker, nmap_scanner):

    """ Проверка успешного запуска async_run"""
    
    mock_create_async_shell_subprocess = mocker.patch('setezor.modules.nmap.scanner.create_async_shell_subprocess', new_callable=AsyncMock)


    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b'<?xml version="1.0"?><nmaprun></nmaprun>', b'')
    
    mock_create_async_shell_subprocess.return_value = mock_process

    extra_args = '-sP 192.168.1.0/24'
    password = 'password'

    mocker.patch.object(nmap_scanner, '_prepare_args', return_value=['nmap'] + [extra_args]) 
    mocker.patch.object(nmap_scanner, '_check_results', return_value={'success': True})

    result = await nmap_scanner.async_run(extra_args, password)

    args_called = mock_create_async_shell_subprocess.call_args[0][0]
    assert args_called == ['sudo', '-S'] + ['nmap'] + [extra_args] 
    assert 'nmap' in args_called

    assert isinstance(result, dict) 
    assert result == {'success': True}  
    mock_create_async_shell_subprocess.assert_called_once()