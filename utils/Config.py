import traceback
import os
import boto3
import constants as _C

class Config:
    
    AWS_SDK = {
        'signature_version': 'v4'
    }

    ADVISOR = {
        'TITLE': 'OTC Service Screener',
        'VERSION': '2.5.0',
        'LAST_UPDATE': '15-May-2026'
    }

    ADMINLTE = {
        'VERSION': '3.1.0',
        'DATERANGE': '2014-2021',
        'URL': 'https://olmo-tech.com',
        'TITLE': 'Olmo Tech Consulting'
    }

    GLOBAL_SERVICES = [
        'iam',
        'cloudfront'
    ]
    
    KEYWORD_SERVICES = [
        'lambda'    
    ]
    
    CURRENT_REGION = 'us-east-1'
    
    # Framework descriptions mapping - includes Spanish descriptions for dashboard and tooltips
    FRAMEWORK_DESCRIPTIONS = {
        'MSR': {
            'name': 'Well-Architected Pillars',
            'spanish': 'Pilares Bien Arquitectados',
            'description': 'Evaluación de 5 pilares: Excelencia Operativa, Seguridad, Confiabilidad, Eficiencia de Desempeño, Optimización de Costos',
            'tooltip': 'Well-Architected Framework - Evaluación de 5 pilares: Excelencia Operativa, Seguridad, Confiabilidad, Eficiencia de Desempeño, Optimización de Costos'
        },
        'FTR': {
            'name': 'Framework Technical Review',
            'spanish': 'Revisión Técnica del Marco',
            'description': 'Revisión Técnica del Marco',
            'tooltip': 'Foundational Technical Review - Análisis profundo de arquitectura técnica'
        },
        'SSB': {
            'name': 'Security Standards Baseline',
            'spanish': 'Línea Base de Estándares de Seguridad',
            'description': 'Conformidad con estándares mínimos de seguridad',
            'tooltip': 'Security Standards Baseline - Conformidad con estándares mínimos de seguridad'
        },
        'WAFS': {
            'name': 'WAF Secure',
            'spanish': 'WAF Seguro',
            'description': 'Validaciones específicas para AWS WAF',
            'tooltip': 'Well-Architected Framework Summary - Validaciones específicas para AWS WAF'
        },
        'CIS': {
            'name': 'CIS Benchmarks',
            'spanish': 'Referencia CIS',
            'description': 'Center for Internet Security - Controles de seguridad',
            'tooltip': 'CIS Benchmarks — Center for Internet Security estándares de seguridad'
        },
        'NIST': {
            'name': 'NIST Cybersecurity',
            'spanish': 'Ciberseguridad NIST',
            'description': 'National Institute of Standards and Technology',
            'tooltip': 'NIST Cybersecurity Framework - Marco de ciberseguridad del Instituto Nacional de Estándares y Tecnología'
        },
        'RMIT': {
            'name': 'RACI Matrix',
            'spanish': 'Matriz RACI',
            'description': 'Matriz de Responsabilidades y Rendición de Cuentas',
            'tooltip': 'Risk Management in Technology (BNM) - Matriz RACI de responsabilidades'
        },
        'SPIP': {
            'name': 'Security Policy Implementation',
            'spanish': 'Implementación de Política de Seguridad',
            'description': 'Cumplimiento de políticas de seguridad',
            'tooltip': 'Security & Privacy Implementation Program - Implementación de Política de Seguridad'
        },
        'RBI': {
            'name': 'Reserve Bank of India',
            'spanish': 'Banco de la Reserva India',
            'description': 'Banco de la Reserva India - Requisitos regulatorios',
            'tooltip': 'Reserve Bank of India Guidelines - Requisitos regulatorios de RBI'
        }
    }
    
    @staticmethod
    def init():
        global cache
        cache = {}
    
    @staticmethod
    def setAccountInfo(__AWS_CONFIG):
        print(" -- Acquiring identify info...")
        
        ssBoto = Config.get('ssBoto', None)
        
        stsClient = ssBoto.client('sts')
        
        resp = stsClient.get_caller_identity()
        stsInfo = {
            'UserId': resp.get('UserId'),
            'Account': resp.get('Account'),
            'Arn': resp.get('Arn')
        }

        Config.set('stsInfo', stsInfo)
        acctId = stsInfo['Account']
        
        adir = 'adminlte/aws/' + acctId
        
        Config.set('HTML_ACCOUNT_FOLDER_FULLPATH', _C.ROOT_DIR + '/' + adir)
        Config.set('HTML_ACCOUNT_FOLDER_PATH', adir)
       
    @staticmethod 
    def set(key, val):
        cache[key] = val

    @staticmethod
    def get(key, defaultValue = False):
        ## <TODO>, fix the DEBUG variable
        DEBUG = False
        if key in cache:
            return cache[key]
        
        if defaultValue == False:
            if DEBUG:
                traceback.print_exc()
        
        return defaultValue
        
    @staticmethod
    def retrieveAllCache():
        return cache
        
    
    ## do checking for prefix=cloud, if found, use first 8character instead
    ## other than that, first 3 prefix should be unique
    @staticmethod
    def getDriversClassPrefix(driver):
        name = Config.extractDriversClassPrefix(driver)
        return 'regionInfo::' + name
    
    @staticmethod
    def extractDriversClassPrefix(driver):
        ## handling for S3
        if driver[:2].lower() == 's3':
            return 's3'
            
        if driver[:7].lower() == 'elastic':
            classPrefix = driver[:10]
        else:
            classPrefix = driver[:3]
            if len(driver) > 3 and driver[:5] == 'cloud':
                classPrefix = driver[:8]
            
        return classPrefix

try:
    if configHasInit:
        pass
except NameError:
    dashboard = {
        'HEALTH_SCORE': {
            'percentage': 0,
            'grade': 'A',
            'raw_score': 0
        }
    }
    Config.init()
    configHasInit = True

if __name__ == "__main__":
    print(os.getcwd())
