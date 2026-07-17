#Connecting PostgreSQL: 

Create a Git Bash alias
Add this to your ~/.bashrc:
    `alias psql='/c/Program\ Files/PostgreSQL/18/bin/psql.exe'`
Reload:
    `source ~/.bashrc`
Then:
    `psql --version`
Running a script: 
    `psql -U postgres -d schema -f src/schema.sql`
run psql server
   `psql -U postgres -d schema`