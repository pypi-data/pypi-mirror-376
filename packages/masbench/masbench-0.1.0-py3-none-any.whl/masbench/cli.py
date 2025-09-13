import typer


app = typer.Typer()


@app.command()
def main():
    """
    Main command for MASBench.
    """
    print("Welcome to MASBench!")


if __name__ == "__main__":
    app()
