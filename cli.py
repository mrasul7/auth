import asyncio
import rich
import typer

from db.database import async_session_maker
from db.models import User
from pydantic import (
    BaseModel, 
    EmailStr, 
    ValidationError
)
from security import hash_password
from sqlalchemy import (
    select, 
    delete
)


class EmailValidate(BaseModel):
    email: EmailStr
    

app = typer.Typer()


async def superadmin_create(
    username: str, 
    email: str, 
    password: str, 
    confirm_password: str
) -> None:
    async with async_session_maker() as session:
        try:
            EmailValidate(email=email)
            db_superadmin = User(
                username=username,
                password=hash_password(password),
                email=email,
                role="superadmin"
            )
            if password != confirm_password:
                rich.print(f"[red][bold]Passwords must be the same! Try again[/bold][/red]")
                return
            
            result = await session.execute(select(User).where(User.role == "superadmin"))
            if result.scalar_one_or_none():
                rich.print(f"[red][bold]Superadmin is already created![/bold][/red]")
                rich.print(f"[purple][bold]Do you want to delete the previous superadmin and create a new one?(y/n)[/bold][/purple]: ")
                answer = input().strip().lower()
                if answer != "y":
                    rich.print(f"[yellow][bold]Operation cancelled.[/bold][/yellow]")
                    return
                
                await session.execute(delete(User).where(User.role == "superadmin"))
                await session.commit()
                
                session.add(db_superadmin)
                await session.commit()
                rich.print(f"[green][bold]The previous superadmin was removed and a new one was added with {username=} and {email=}[/bold][/green]")             
            
            session.add(db_superadmin)
            await session.commit()
            rich.print(f"[green][bold]Superadmin created successfully![/bold][/green]")
        except ValidationError:
            rich.print(f"[red][bold]Invalid email! Try again![/bold][/red]")
            typer.echo("Invalid email")
        except Exception as e:
            await session.rollback()
            rich.print(f"[red][bold]Error {e}[/bold][/red]")
        finally:
            await session.close()


@app.command()
def create_superadmin(
    username = typer.Argument(..., help="Username for superadmin: "),
    email: str = typer.Argument(..., help="Email for superadmin: "),
    password = typer.Argument(..., help="Password for superadmin: "),
    confirm_password = typer.Argument(..., help="Confirm password: ")
) -> None:
    asyncio.run(superadmin_create(username, email, password, confirm_password))


if __name__ == "__main__":
    app()