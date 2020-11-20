import typer

app = typer.Typer()


@app.command()
def create():
    raise NotImplementedError


@app.command()
def delete():
    raise NotImplementedError


@app.command()
def describe():
    raise NotImplementedError


@app.command("list")
def list_():
    raise NotImplementedError


@app.command()
def update():
    raise NotImplementedError
