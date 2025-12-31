
from services.scheduler.input_parser import InputParser
parser = InputParser()
agents = parser.parse_excel(r'c:\Users\hagudelor\VSCode\em_sipo\Plantilla_Agentes_Leroy.xlsx')
for a in agents[:10]:
    print(f"Agent: {a['name']}, Contract: {a['contract_hours']}")
