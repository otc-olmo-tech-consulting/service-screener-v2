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
    
    # Default client name (can be overridden via --client CLI flag)
    CLIENT_NAME = 'OTC'

    GLOBAL_SERVICES = [
        'iam',
        'cloudfront'
    ]
    
    KEYWORD_SERVICES = [
        'lambda'    
    ]
    
    CURRENT_REGION = 'us-east-1'
    
    # Scan timestamp - set when scanning begins
    SCAN_TIMESTAMP = None
    
    # Framework descriptions mapping - includes Spanish descriptions for dashboard and tooltips
    # Framework descriptions. The report currently renders the English fields
    # ('description' / 'tooltip'). The Spanish equivalents are preserved in
    # 'spanish', 'description_es' and 'tooltip_es' so a future language selector
    # can switch the whole report to Spanish without re-translating.
    FRAMEWORK_DESCRIPTIONS = {
        'MSR': {
            'name': 'Well-Architected Pillars',
            'spanish': 'Pilares Bien Arquitectados',
            'description': 'Assessment of 5 pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization',
            'description_es': 'Evaluación de 5 pilares: Excelencia Operativa, Seguridad, Confiabilidad, Eficiencia de Desempeño, Optimización de Costos',
            'tooltip': 'Well-Architected Framework - Assessment of 5 pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization',
            'tooltip_es': 'Well-Architected Framework - Evaluación de 5 pilares: Excelencia Operativa, Seguridad, Confiabilidad, Eficiencia de Desempeño, Optimización de Costos'
        },
        'FTR': {
            'name': 'Framework Technical Review',
            'spanish': 'Revisión Técnica del Marco',
            'description': 'Technical Framework Review',
            'description_es': 'Revisión Técnica del Marco',
            'tooltip': 'Foundational Technical Review - In-depth analysis of technical architecture',
            'tooltip_es': 'Foundational Technical Review - Análisis profundo de arquitectura técnica'
        },
        'SSB': {
            'name': 'Security Standards Baseline',
            'spanish': 'Línea Base de Estándares de Seguridad',
            'description': 'Conformance with minimum security standards',
            'description_es': 'Conformidad con estándares mínimos de seguridad',
            'tooltip': 'Security Standards Baseline - Conformance with minimum security standards',
            'tooltip_es': 'Security Standards Baseline - Conformidad con estándares mínimos de seguridad'
        },
        'WAFS': {
            'name': 'WAF Secure',
            'spanish': 'WAF Seguro',
            'description': 'AWS WAF-specific validations',
            'description_es': 'Validaciones específicas para AWS WAF',
            'tooltip': 'Well-Architected Framework Summary - AWS WAF-specific validations',
            'tooltip_es': 'Well-Architected Framework Summary - Validaciones específicas para AWS WAF'
        },
        'CIS': {
            'name': 'CIS Benchmarks',
            'spanish': 'Referencia CIS',
            'description': 'Center for Internet Security - Security controls',
            'description_es': 'Center for Internet Security - Controles de seguridad',
            'tooltip': 'CIS Benchmarks — Center for Internet Security standards',
            'tooltip_es': 'CIS Benchmarks — Center for Internet Security estándares de seguridad'
        },
        'NIST': {
            'name': 'NIST Cybersecurity',
            'spanish': 'Ciberseguridad NIST',
            'description': 'National Institute of Standards and Technology',
            'description_es': 'National Institute of Standards and Technology',
            'tooltip': 'NIST Cybersecurity Framework - Cybersecurity framework from the National Institute of Standards and Technology',
            'tooltip_es': 'NIST Cybersecurity Framework - Marco de ciberseguridad del Instituto Nacional de Estándares y Tecnología'
        },
        'RMIT': {
            'name': 'RACI Matrix',
            'spanish': 'Matriz RACI',
            'description': 'Responsibility and Accountability Matrix',
            'description_es': 'Matriz de Responsabilidades y Rendición de Cuentas',
            'tooltip': 'Risk Management in Technology (BNM) - RACI responsibility matrix',
            'tooltip_es': 'Risk Management in Technology (BNM) - Matriz RACI de responsabilidades'
        },
        'SPIP': {
            'name': 'Security Policy Implementation',
            'spanish': 'Implementación de Política de Seguridad',
            'description': 'Compliance with security policies',
            'description_es': 'Cumplimiento de políticas de seguridad',
            'tooltip': 'Security & Privacy Implementation Program - Security policy implementation',
            'tooltip_es': 'Security & Privacy Implementation Program - Implementación de Política de Seguridad'
        },
        'RBI': {
            'name': 'Reserve Bank of India',
            'spanish': 'Banco de la Reserva India',
            'description': 'Reserve Bank of India - Regulatory requirements',
            'description_es': 'Banco de la Reserva India - Requisitos regulatorios',
            'tooltip': 'Reserve Bank of India Guidelines - RBI regulatory requirements',
            'tooltip_es': 'Reserve Bank of India Guidelines - Requisitos regulatorios de RBI'
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
    
    @staticmethod
    def get_client_name():
        """Get the configured client name for branding"""
        return Config.get('CLIENT_NAME', Config.CLIENT_NAME)
    
    @staticmethod
    def set_client_name(name):
        """Set the client name for branding"""
        Config.set('CLIENT_NAME', name)
        
    
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
