import sys
import click
from core.shell import run_shell
from core.commands import (
    check_handler, explain_handler, ask_handler, fix_handler,
    run_handler, generate_handler, snippet_handler
)

@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        run_shell()
    else:
        pass  # Subcommand will handle

@main.command()
@click.argument('file', type=click.Path(exists=True))
def check(file):
    ok, messages = check_handler(file)
    if ok:
        click.echo("Syntax OK")
        sys.exit(0)
    else:
        for msg in messages:
            click.echo(msg)
        sys.exit(1)

@main.command()
@click.argument('file', type=click.Path(exists=True))
def explain(file):
    result = explain_handler(file)
    click.echo(result)

@main.command()
@click.argument('question', nargs=-1)
def ask(question):
    question = ' '.join(question)
    result = ask_handler(question)
    click.echo(result)

@main.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--apply', is_flag=True, help='Apply fixes to file')
def fix(file, apply):
    result, diff, new_code = fix_handler(file)
    click.echo(diff)
    if apply:
        with open(file, 'w') as f:
            f.write(new_code)
        click.echo("Changes applied.")

@main.command()
@click.argument('command', nargs=-1)
def run(command):
    command = ' '.join(command)
    exit_code, stdout, stderr = run_handler(command)
    click.echo(f"STDOUT:\n{stdout}")
    click.echo(f"STDERR:\n{stderr}")
    click.echo(f"Exit code: {exit_code}")
    sys.exit(exit_code)

@main.command('generate')
@click.argument('type')
@click.argument('template')
@click.argument('name')
def generate_cmd(type, template, name):
    if type != 'project':
        click.echo("Only 'project' supported.")
        sys.exit(1)
    generate_handler(template, name)
    click.echo(f"Project {name} generated.")

@main.command('snippet')
@click.argument('action', type=click.Choice(['add', 'list', 'remove']))
@click.argument('name', required=False)
@click.argument('content', required=False, nargs=-1)
def snippet_cmd(action, name, content):
    content = ' '.join(content) if content else None
    result = snippet_handler(action, name, content)
    click.echo(result)

if __name__ == '__main__':
    main()