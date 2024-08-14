import xmltodict

class XMLParser:
    
    @classmethod
    def parse_xml(cls, data: str):
        return xmltodict.parse(data)
    
    @classmethod
    def pop_params(cls, data: dict):
        
        params_key = [i for i in data.keys() if i.startswith('@')]
        result = {}
        for key in params_key:
            value = data.pop(key)
            result[key[1:]] = value
        return result