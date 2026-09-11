from elephantine.client import ElephantineClient

client = ElephantineClient("http://127.0.0.1:8765")
client.remember("Database is PostgreSQL 16", workspace_id="team-1", role_authority=1.0)
res = client.recall("database engine", workspace_id="team-1")
print(res)
