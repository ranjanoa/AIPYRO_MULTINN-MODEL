IS_PRODUCTION = True

DB_CONF = {
    "url": "http://localhost:8086",     
    "token": "JMX7b7QQW6FqipQI8A4LICEIL2BXU8ymaLFdtkD7btb4nXEywT2Wa_cpBOMOEVtjPMhYm_PiJEFwRsxmjmNT6A==",  
    "org": "MyPlant"
}

# Database tables
BUCKET = "cimporAI"           
MEASUREMENT = "kiln1"
RESULT_MEASUREMENT = "cimpor_data_results"

# Deployment settings (customer environment)
FLASK_HOST = "0.0.0.0"     
FLASK_PORT = 5500          
START_TIME_MARKER = "2025-04-13T05:01:15Z" 

