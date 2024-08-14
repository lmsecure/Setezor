import click
from crt4 import CertInfo
import pandas as pd
import asyncio
import json


@click.group()
def cli():
    pass

@cli.command()
@click.argument('host')
@click.option('-p', '--port', default="443", help="port, default 443")
def scan(port, host):
    cert = CertInfo.get_cert_and_parse(host=host, port=port)
    print(json.dumps(cert, ensure_ascii=False, indent="  "))


@cli.command()
@click.option('-if', '--input_file', type=click.Path(exists=True), help='CSV file with structure "host,port"')
@click.option('-of', '--output_file', default="output", help="name of output file")
def dump(input_file, output_file):
    async def dump_pre(filename, output):
        df = pd.read_csv(filename) 
        for i in df.to_dict('records'):
            await CertInfo.write_to_jsonfile(host=i.get('host'), port=i.get('port'), filename=output)
        
    loop = asyncio.get_event_loop() 
    loop.run_until_complete(dump_pre(input_file, output_file))

            
cli.add_command(scan)
cli.add_command(dump)    


if __name__ == '__main__':
    cli()