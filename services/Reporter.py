import os
import json
import re

from utils.Config import Config
import utils.Config as cfg
from utils.Tools import _warn, _info
import constants as _C


def calculate_health_score(severity_counts):
    """
    Calculate health score from severity distribution.
    
    Args:
        severity_counts: dict with keys 'H', 'M', 'L', 'I' and counts
    
    Returns:
        dict with 'percentage', 'grade', 'raw_score'
    """
    total_findings = sum(severity_counts.values())
    
    # If no findings, return perfect score
    if total_findings == 0:
        return {
            'percentage': 100.0,
            'grade': 'A',
            'raw_score': 0
        }
    
    # Weighted formula: (H × 3) + (M × 1.5) + (L × 0.5)
    raw_score = (severity_counts.get('H', 0) * 3) + \
                (severity_counts.get('M', 0) * 1.5) + \
                (severity_counts.get('L', 0) * 0.5)
    
    # Maximum possible score (all findings are High severity)
    max_possible = total_findings * 3
    
    # Calculate health percentage using formula: 100 - (raw_score / max_possible × 100)
    # This inverts the scale so higher percentage = better health
    health_percentage = 100 - (raw_score / max_possible * 100)
    health_percentage = max(0, round(health_percentage, 1))
    
    # Grade mapping (A=90-100%, B=80-89%, C=70-79%, D=60-69%, F<60%)
    if health_percentage >= 90:
        grade = 'A'
    elif health_percentage >= 80:
        grade = 'B'
    elif health_percentage >= 70:
        grade = 'C'
    elif health_percentage >= 60:
        grade = 'D'
    else:
        grade = 'F'
    
    return {
        'percentage': health_percentage,
        'grade': grade,
        'raw_score': round(raw_score, 2)
    }


def extract_top_critical_findings(limit=5):
    """
    Extract top N critical (HIGH severity) findings from aggregated dashboard results.
    
    This function collects all HIGH severity findings from the dashboard data structure,
    sorted by the number of affected resources (most impactful first).
    
    The findings are aggregated by (service, rule) to show the most critical issues
    with their descriptions.
    
    Args:
        limit: Maximum number of findings to return (default: 5)
    
    Returns:
        List of dicts with structure:
        {
            'rank': int (1-based),
            'service': str (service name),
            'rule': str (check/rule ID),
            'description': str (finding description),
            'severity': str ('H' for HIGH),
            'affected_resources': int (count of affected resources)
        }
        
        If no HIGH severity findings exist, returns an empty list.
    """
    dashboard = cfg.dashboard
    top_findings = []
    finding_dict = {}  # Dict to aggregate findings by (service, rule)
    
    # Collect reporter instances from Config
    # The reporters have been stored during service scanning
    service_reporters = Config.get('service_reporters', {})
    
    # Extract HIGH severity findings from service reporters
    for service, reporter in service_reporters.items():
        if not hasattr(reporter, 'summaryRegion') or not hasattr(reporter, 'config'):
            continue
        
        # Iterate through all rules with failures
        for rule_id, regions_dict in reporter.summaryRegion.items():
            # Check if this rule has HIGH severity
            if reporter._checkCriticality(rule_id) != 'H':
                continue
            
            # Count total affected resources for this rule
            total_affected = 0
            for region, identifiers in regions_dict.items():
                total_affected += len(identifiers)
            
            if total_affected > 0:
                # Get rule description from config
                description = reporter._getConfigValue(rule_id, '^description') or 'No description available'
                
                # Create finding entry (use rule_id as key to aggregate)
                finding_key = f"{service}::{rule_id}"
                
                if finding_key not in finding_dict:
                    finding_dict[finding_key] = {
                        'service': service,
                        'rule': rule_id,
                        'description': description,
                        'severity': 'H',
                        'affected_resources': total_affected
                    }
    
    # Convert dict to sorted list
    finding_list = list(finding_dict.values())
    
    # Sort by affected_resources count (descending) to get most impactful first
    sorted_findings = sorted(
        finding_list,
        key=lambda x: x['affected_resources'],
        reverse=True
    )
    
    # Limit to top N and add rank
    for rank, finding in enumerate(sorted_findings[:limit], 1):
        finding['rank'] = rank
        top_findings.append(finding)
    
    return top_findings

class Reporter:
    def __init__(self, service):
        self.summary = {}
        self.summaryRegion = {}
        self.detail = {}
        self.config = {}
        self.charts = {}
        self.chartsConfig = {}
        self.service = service
        self.warningList = []
        self.stats = {}
        self.findingsCount = 0
        self.suppressedCount = 0
        
        # Track suppressed items for reporting
        self.suppressedSummary = {}
        self.suppressedSummaryRegion = {}
        self.suppressedDetail = {}
        self.suppressedCardSummary = {}
        
        # Track severity counts for health score calculation
        self.severity_counts = {'H': 0, 'M': 0, 'L': 0, 'I': 0}
        
        folder = service
        if service in Config.KEYWORD_SERVICES:
            folder = service + '_'
        
        serviceReporterJsonPath = _C.SERVICE_DIR + '/' + folder + '/' + service + '.reporter.json'
        serviceChartJsonPath = _C.SERVICE_DIR + '/' + folder + '/' + service + '.chart.json'
        
        if not os.path.exists(serviceReporterJsonPath):
            print("[Fatal] " + serviceReporterJsonPath + " not found")
        self.config = json.loads(open(serviceReporterJsonPath).read())
        if not self.config:
            raise Exception(serviceReporterJsonPath + " does not contain valid JSON")
        generalConfig = json.loads(open(_C.GENERAL_CONF_PATH).read())
        self.config = {**self.config, **generalConfig}
        
        ## KPI Building
        self.acquireStatInfo()
        
    def acquireStatInfo(self):
        checksCount = 0
        
        statpath = _C.FORK_DIR + '/' + self.service + '.stat.json'
        f = open(statpath, "r")
        stats = json.loads(f.read())
        f.close()
        
        infopath = _C.ROOT_DIR + '/' + 'info.json'
        f = open(infopath, "r")
        checks = json.loads(f.read())
        if not self.service in checks:
            _warn( "[{}] is not available in checks, please submit an issue to github to update info.json through RuleCount.py.".format(self.service))
        else:
            checksCount = checks[self.service]
            
        stats['checksCount'] = checksCount
        self.stats = stats
            

    def process(self, serviceObjs):
        dashboard = cfg.dashboard
        
        # Ensure HEALTH_SCORE structure is always present
        if 'HEALTH_SCORE' not in dashboard:
            dashboard['HEALTH_SCORE'] = {
                'percentage': 0,
                'grade': 'A',
                'raw_score': 0
            }
        
        total_suppressed = 0
        
        for region, objs in serviceObjs.items():
            region_suppressed = 0
            
            for identifier, results in objs.items():
                suppressed = self._process(region, identifier, results)
                region_suppressed += suppressed
                total_suppressed += suppressed
                
            if 'SERV' not in dashboard:
                dashboard['SERV'] = {self.service: {region: {}}}
                
            if self.service not in dashboard['SERV']:
                dashboard['SERV'][self.service] = {region: {}}
                
            dashboard['SERV'][self.service][region] = {'Total': len(objs), 'H': 0}
            
            if region_suppressed > 0:
                print(f"[SUMMARY] Suppressed {region_suppressed} findings in region {region} for service {self.service}")
        
        if total_suppressed > 0:
            print(f"[TOTAL] Suppressed {total_suppressed} findings for service {self.service}")
            
        return self
        
    def getDetail(self):
        return self.detail
    
    def getCard(self):
        return self.cardSummary
    
    def getSuppressedSummary(self):
        """Get summary of suppressed findings for reporting"""
        return self.suppressedSummary
    
    def getSuppressedDetail(self):
        """Get detailed suppressed findings for reporting"""
        return self.suppressedDetail
    
    def getSuppressedCardSummary(self):
        """Get card summary for suppressed findings"""
        return getattr(self, 'suppressedCardSummary', {})
    
    def _process(self, region, identifier, results):
        # Get suppressions manager if available
        suppressions_manager = Config.get('suppressions_manager', None)
        suppressed_count = 0
        
        for key, info in results.items():
            # Check if this finding should be suppressed BEFORE processing
            if suppressions_manager:
                if suppressions_manager.is_suppressed(self.service, key, identifier):
                    # Track suppressed finding for reporting
                    print(f"[SUPPRESSED] {self.service}:{key} for resource {identifier}")
                    suppressed_count += 1
                    
                    # Only track suppressed findings that are failures (status -1)
                    if info[0] == -1:
                        # Register suppressed summary info
                        if key not in self.suppressedSummaryRegion:
                            self.suppressedSummaryRegion[key] = {}
                            self.suppressedSummary[key] = []
                            
                        if region not in self.suppressedSummaryRegion[key]:
                            self.suppressedSummaryRegion[key][region] = []
                        
                        self.suppressedSummaryRegion[key][region].append(identifier)
                        self.suppressedSummary[key].append(identifier)
                        
                        if region not in self.suppressedDetail:
                            self.suppressedDetail[region] = {}
                        
                        if identifier not in self.suppressedDetail[region]:
                            self.suppressedDetail[region][identifier] = {}
                            
                        self.suppressedDetail[region][identifier][key] = info[1]
                    
                    continue
            
            # Only process findings that are failures (status -1)
            if info[0] == -1:
                ## Register summary info
                if key not in self.summaryRegion:
                    self.summaryRegion[key] = {}
                    self.summary[key] = []
                    
                if region not in self.summaryRegion[key]:
                    self.summaryRegion[key][region] = []
                
                self.summaryRegion[key][region].append(identifier)
                self.summary[key].append(identifier)
                
                if region not in self.detail:
                    self.detail[region] = {}
                
                if identifier not in self.detail[region]:
                    self.detail[region][identifier] = {}
                    
                # print(identifier, key, info[1])
                self.detail[region][identifier][key] = info[1]
                
        # Store the total suppressed count for this service
        self.suppressedCount += suppressed_count
        
        return suppressed_count

    def _getConfigValue(self, check, field):
        if check not in self.config:
            k = self.service + '::' + check
            if not k in self.warningList:
                _warn("Rule {}::{} is not available in reporter, please submit an issue to github.".format(self.service, check) )
                self.warningList.append(k)
            return None
        
        if field == 'category' and field not in self.config[check]:
            field = '__categoryMain'
        
        if field not in self.config[check]:
            k = self.service + '::' + check + '::' + field
            if not k in self.warningList:
                _warn("Rule {}::{} available in reporter, but missing {}, please submit an issue to github.".format(self.service, check, field) )
                self.warningList.append(k)
            return None
        
        return self.config[check][field]
    
    def _checkCriticality(self, check):
        return self._getConfigValue(check, 'criticality') or 'X'
    
    def _checkCategory(self, check):
        return self._getConfigValue(check, 'category') or 'X'
        
    def getSummary(self):
        # Enhance for MAP summary
        # _ : refers to HIGH category
        dashboard = cfg.dashboard
        if 'MAP' not in dashboard:
            dashboard['MAP'] = {}
            
        dashboard['MAP'][self.service] = {
            '_': {
                'S': 0,
                'C': 0,
                'R': 0,
                'P': 0,
                'O': 0    
            },
            'H': 0,
            'M': 0,
            'L': 0,
            'I': 0,
            'S': 0,
            'C': 0,
            'R': 0,
            'P': 0,
            'O': 0    
        }

        for check, dataSet in self.summaryRegion.items():
            for region, obj in dataSet.items():
                itemSize = len(obj)

                #check criticality
                category = self._checkCategory(check)
                mainCategory = category[0]
                if mainCategory == 'T':
                    continue
                
                critical = self._checkCriticality(check)
                
                if 'CRITICALITY' not in dashboard:
                    dashboard['CRITICALITY'] = {}
                if region not in dashboard['CRITICALITY']:
                    dashboard['CRITICALITY'][region] = {}
                if critical not in dashboard['CRITICALITY'][region]:
                    dashboard['CRITICALITY'][region][critical] = 0
                    
                dashboard['CRITICALITY'][region][critical] += itemSize
                
                # Track severity counts for health score calculation
                if critical in self.severity_counts:
                    self.severity_counts[critical] += itemSize

                if critical == 'H':
                    dashboard['SERV'][self.service][region]['H'] += itemSize

                #check category
                category = self._checkCategory(check)
                mainCategory = category[0]
                
                if 'CATEGORY' not in dashboard:
                    dashboard['CATEGORY'] = {}
                if region not in dashboard['CATEGORY']:
                    dashboard['CATEGORY'][region] = {}
                if mainCategory not in dashboard['CATEGORY'][region]:
                    dashboard['CATEGORY'][region][mainCategory] = {'H': 0, 'M': 0, 'L': 0, 'I': 0}
                
                dashboard['CATEGORY'][region][mainCategory][critical] += itemSize

                # Enhance for MAP summary
                if mainCategory == 'T':
                    continue

                if critical == 'H':
                    dashboard['MAP'][self.service]['_'][mainCategory] += itemSize
                else:
                    pass
                
                if critical == 'X':
                    ## Error handling in _getConfigValue
                    break
                else:
                    dashboard['MAP'][self.service][critical] += itemSize
                    dashboard['MAP'][self.service][mainCategory] += itemSize

        self.cardSummary = {}
        service = self.service
        
        sorted(self.summary)
        for check, items in self.summary.items():
            if check not in self.config:
                # print("<{}> not exists in {}.reporter.json".format(check, service))
                continue
            
            self.cardSummary[check] = self.config[check]
            
            # Process Field by Field:
            # Process description
            desc = self._getConfigValue(check, '^description')
            if desc:
                COUNT = len(items)
                COUNT = "<strong><u>{}</u></strong>".format(COUNT)
                self.cardSummary[check]['^description'] = desc.replace('{$COUNT}', COUNT)
            
            # Process category
            category = self._getConfigValue(check, 'category')
            if category:
                self.cardSummary[check]['__categoryMain'] = category[0]
                if len(category) > 1:
                    self.cardSummary[check]['__categorySub'] = category[1:]
                
                del self.cardSummary[check]['category']
            
            # Process ref
            ref = self._getConfigValue(check, 'ref')
            if ref and isinstance(ref, list):
                links = []
                for link in ref:
                    output = re.search(r'\[(.*)\]<(.*)>', link)
                    if not output:
                        print(f"  [WARNING] Invalid ref syntax in {self.service}/{check}: '{link}'")
                        continue
                    
                    links.append("<a href='{}'>{}</a>".format(output.group(2), output.group(1)))
                
                self.cardSummary[check]['__links'] = links
                del self.cardSummary[check]['ref']
                
            resourceByRegion = {}
            for region, insts in self.summaryRegion[check].items():
                self.findingsCount += len(insts)
                resourceByRegion[region] = insts
                
            self.cardSummary[check]['__affectedResources'] = resourceByRegion
        
        # Generate suppressed card summary while config is still available
        self.suppressedCardSummary = {}
        for check, items in self.suppressedSummary.items():
            if check not in self.config:
                continue
            
            self.suppressedCardSummary[check] = self.config[check].copy()
            
            # Process Field by Field:
            # Process description
            desc = self._getConfigValue(check, '^description')
            if desc:
                COUNT = len(items)
                COUNT = "<strong><u>{}</u></strong>".format(COUNT)
                self.suppressedCardSummary[check]['^description'] = desc.replace('{$COUNT}', COUNT)
            
            # Process category
            category = self._getConfigValue(check, 'category')
            if category:
                self.suppressedCardSummary[check]['__categoryMain'] = category[0]
                if len(category) > 1:
                    self.suppressedCardSummary[check]['__categorySub'] = category[1:]
                
                if 'category' in self.suppressedCardSummary[check]:
                    del self.suppressedCardSummary[check]['category']
            
            # Process ref
            ref = self._getConfigValue(check, 'ref')
            if ref and isinstance(ref, list):
                links = []
                for link in ref:
                    output = re.search(r'\[(.*)\]<(.*)>', link)
                    if not output:
                        print(f"  [WARNING] Invalid ref syntax in {self.service}/{check} (suppressed): '{link}'")
                        continue
                    
                    links.append("<a href='{}'>{}</a>".format(output.group(2), output.group(1)))
                
                self.suppressedCardSummary[check]['__links'] = links
                if 'ref' in self.suppressedCardSummary[check]:
                    del self.suppressedCardSummary[check]['ref']
                
            resourceByRegion = {}
            for region, insts in self.suppressedSummaryRegion[check].items():
                resourceByRegion[region] = insts
                
            self.suppressedCardSummary[check]['__affectedResources'] = resourceByRegion
            
        del self.summaryRegion
        del self.summary
        del self.suppressedSummaryRegion
        del self.suppressedSummary
        
        # Calculate and store health score in dashboard
        health_score = calculate_health_score(self.severity_counts)
        if 'HEALTH_SCORE' not in dashboard:
            dashboard['HEALTH_SCORE'] = {}
        dashboard['HEALTH_SCORE'] = health_score
        
        return self
        
    def getDetails(self):
        tmp = {}
        for region, detail in self.detail.items():
            for identifier, checks in detail.items():
                # htmlAttribute = "data-resource='" + identifier + "' data-region='" + region + "'"
                sorted(checks)
                # del tmp[region][identifier]
                for key, info in checks.items():
                    arr = self.getDetailAttributeByKey(key)
                    arr['value'] = info
                    # self.detail[region][identifier][key] = arr
                    if region not in tmp:
                        tmp[region] = {}
                    
                    if identifier not in tmp[region]:
                        tmp[region][identifier] = {}
                        #tmp[region][identifier] = {key: arr}
                    
                    if key not in tmp[region][identifier]:
                        tmp[region][identifier][key] = arr
                    
        self.detail = tmp.copy()
        # print(self.detail)
        
        del self.config
        
    def getDetailAttributeByKey(self, key):
        config = {}
        if not key in config:
            arr = {
                'category': self._getConfigValue(key, 'category'),
                'criticality': self._getConfigValue(key, 'criticality'),
                'shortDesc': self._getConfigValue(key, 'shortDesc')
            }
            
            category = arr['category']
            if category:
                arr['__categoryMain'] = category[0]
                if len(category) > 1:
                    arr['__categorySub'] = category[1:]
                
                del arr['category']
            
            config[key] = arr
        
        return config[key]
        
    def resetDashboard(self):
        cfg.dashboard = {}

    ## Process Data for Charts
    ## <TO DO> Enhance to support bar charts data and grouping without region
    def processCharts(self, chartsObjs):
        for region in chartsObjs:
            chartDetails = chartsObjs[region]
            configList = chartDetails['config']
            dataList = chartDetails['data']
            
            for chartTitle in configList:
                if chartTitle not in self.chartsConfig:
                    self.chartsConfig[chartTitle] = {}

                if not self.chartsConfig[chartTitle]:
                    self.chartsConfig[chartTitle] = configList[chartTitle]
                else:
                    mergedLegends = list(set(self.chartsConfig[chartTitle]['legends']).union(set(configList[chartTitle]['legends'])))
                    self.chartsConfig[chartTitle]['legends'] = mergedLegends
            

            for chartTitle in dataList:
                if chartTitle not in self.charts:
                    self.charts[chartTitle] = {}
                
                if region not in self.charts[chartTitle]:
                    self.charts[chartTitle][region] = {}
                
                self.charts[chartTitle][region] = dataList[chartTitle]


        
        return self
