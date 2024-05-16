import click

@click.command()
@click.option('-h', '--host', default='0.0.0.0', type=str, show_default=True, help='Host to web-server')
@click.option('-p', '--port', default=16661, type=int, show_default=True, help='Number of port to binding')
def run_app(host: str, port: int):
    from aiohttp import web
    from exceptions.loggers import get_logger, LoggerNames
    from setezor import create_app, print_banner, create_ssl_context
    web.run_app(app=create_app(host=host, port=port), host=host, port=port, 
                access_log=get_logger(LoggerNames.web_server, handlers=['file']), 
                print=print_banner(host, port),
                ssl_context=create_ssl_context())
    
if __name__ == '__main__':
    run_app()