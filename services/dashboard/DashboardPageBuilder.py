import datetime
from services.PageBuilder import PageBuilder
from utils.Config import Config
import utils.Config as cfg

class DashboardPageBuilder(PageBuilder):
    def init(self):
        self.isHome = True
        self.template = 'dashboard'
    
    def get_health_color_and_status(self, grade):
        """
        Map health score grade to Bootstrap color class and status label.
        
        Args:
            grade: Health grade ('A', 'B', 'C', 'D', 'F')
            
        Returns:
            tuple: (color_class, status_label) for Bootstrap styling
        """
        mapping = {
            'A': ('success', 'Excellent'),
            'B': ('info', 'Good Standing'),
            'C': ('warning', 'Improvements Required'),
            'D': ('warning', 'Improvements Required'),
            'F': ('danger', 'Needs Immediate Attention')
        }
        return mapping.get(grade, ('secondary', 'Unknown'))
    
    def generateHealthScoreCard(self):
        """
        Generate the enhanced health score card with executive narrative (Task 2.14).
        
        Renders a prominent card with:
        - Executive Spanish terminology for grades
        - Critical findings count subtitle
        - Timestamp and account ID footer
        - Mini-tiles for H/M/L severity counts
        - Horizontal progress bar with 50%/75% markers
        - Dynamic gradient coloring
        
        Returns:
            str: HTML for enhanced health score card
        """
        dashboard = cfg.dashboard.copy()
        health_score = dashboard.get('HEALTH_SCORE', {})
        
        # Extract health score values with defaults
        percentage = health_score.get('percentage', 100)
        grade = health_score.get('grade', 'A').upper()
        raw_score = health_score.get('raw_score', 0)
        
        # Format percentage with 1 decimal place
        if isinstance(percentage, (int, float)):
            percentage_str = f"{percentage:.1f}"
            percentage_val = float(percentage)
        else:
            percentage_str = "100.0"
            percentage_val = 100.0
        
        # Get severity counts from dashboard
        severity_counts = {'H': 0, 'M': 0, 'L': 0}
        hri_sets = {'H': 0, 'M': 0, 'L': 0, 'I': 0}
        total_findings = 0
        
        if 'CRITICALITY' in dashboard:
            for region, details in dashboard['CRITICALITY'].items():
                for cat, cnt in details.items():
                    if cat in hri_sets:
                        hri_sets[cat] += cnt
                        total_findings += cnt
        
        # Extract H, M, L counts
        severity_counts['H'] = hri_sets.get('H', 0)
        severity_counts['M'] = hri_sets.get('M', 0)
        severity_counts['L'] = hri_sets.get('L', 0)
        
        # Get account ID and current timestamp
        account_id = Config.get('accountId', 'N/A')
        current_time = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        # Grade terminology and gradient colors.
        # NOTE: both 'english' and 'spanish' labels are kept here on purpose so a
        # future language selector can switch between them. Today the report renders
        # the English label ('english'); the Spanish scaffolding stays intact.
        grade_map = {
            'A': {
                'english': 'Optimal Posture',
                'spanish': 'Postura Óptima',
                'gradient_start': '#28a745',
                'gradient_end': '#20c997',
                'color_class': 'success'
            },
            'B': {
                'english': 'Good Posture',
                'spanish': 'Postura Buena',
                'gradient_start': '#0066cc',
                'gradient_end': '#0099ff',
                'color_class': 'info'
            },
            'C': {
                'english': 'Improvements Required',
                'spanish': 'Requiere Mejoras',
                'gradient_start': '#ff9900',
                'gradient_end': '#ffb84d',
                'color_class': 'warning'
            },
            'D': {
                'english': 'Improvements Required',
                'spanish': 'Requiere Mejoras',
                'gradient_start': '#ff9900',
                'gradient_end': '#ffb84d',
                'color_class': 'warning'
            },
            'F': {
                'english': 'Needs Immediate Attention',
                'spanish': 'Atención Urgente',
                'gradient_start': '#dc3545',
                'gradient_end': '#ff6b6b',
                'color_class': 'danger'
            }
        }
        
        grade_info = grade_map.get(grade, grade_map['F'])
        grade_label = grade_info['english']
        gradient_start = grade_info['gradient_start']
        gradient_end = grade_info['gradient_end']
        color_class = grade_info['color_class']
        
        # Calculate marker positions for progress bar (50% and 75%)
        marker_50 = 50
        marker_75 = 75
        
        # Build HTML for health score card with all enhancements
        card_html = f"""
<div class="row" style="margin-bottom: 20px;">
    <div class="col-md-12">
        <div class="card" style="border: none; box-shadow: 0 4px 8px rgba(0,0,0,0.15); overflow: hidden;">
            <!-- Card Header with Gradient -->
            <div style="background: linear-gradient(135deg, {gradient_start} 0%, {gradient_end} 100%); padding: 25px; color: white;">
                <div class="row" style="align-items: center;">
                    <div class="col-md-6">
                        <h4 style="margin: 0 0 8px 0; font-weight: bold; color: rgba(255,255,255,0.95);">AWS Environment Operational Health</h4>
                        <p style="margin: 0; font-size: 0.9em; color: rgba(255,255,255,0.8);">{severity_counts['H']} critical findings require immediate action · {total_findings} total findings</p>
                    </div>
                    <div class="col-md-6" style="text-align: right;">
                        <div style="font-size: 2.8em; font-weight: bold; color: rgba(255,255,255,1); margin: 0; line-height: 1;">{percentage_str}%</div>
                        <div style="font-size: 1.15em; font-weight: 600; color: rgba(255,255,255,0.95); margin-top: 5px;">{grade_label}</div>
                    </div>
                </div>
            </div>
            
            <!-- Card Body with Mini-tiles and Progress Bar -->
            <div class="card-body" style="padding: 20px;">
                <!-- Mini-tiles for H/M/L counts -->
                <div class="row" style="margin-bottom: 20px; gap: 10px;">
                    <div class="col-auto" style="flex: 0 1 calc(33.333% - 7px); text-align: center; padding: 10px; background-color: #f8f9fa; border-radius: 6px; border-left: 4px solid #dc3545;">
                        <div style="font-size: 1.5em; font-weight: bold; color: #dc3545;">
                            <i class="fas fa-ban"></i> {severity_counts['H']}
                        </div>
                        <div style="font-size: 0.85em; color: #666; margin-top: 4px;">Critical</div>
                    </div>
                    <div class="col-auto" style="flex: 0 1 calc(33.333% - 7px); text-align: center; padding: 10px; background-color: #f8f9fa; border-radius: 6px; border-left: 4px solid #ffc107;">
                        <div style="font-size: 1.5em; font-weight: bold; color: #ffc107;">
                            <i class="fas fa-exclamation-triangle"></i> {severity_counts['M']}
                        </div>
                        <div style="font-size: 0.85em; color: #666; margin-top: 4px;">Moderate</div>
                    </div>
                    <div class="col-auto" style="flex: 0 1 calc(33.333% - 7px); text-align: center; padding: 10px; background-color: #f8f9fa; border-radius: 6px; border-left: 4px solid #17a2b8;">
                        <div style="font-size: 1.5em; font-weight: bold; color: #17a2b8;">
                            <i class="fas fa-eye"></i> {severity_counts['L']}
                        </div>
                        <div style="font-size: 0.85em; color: #666; margin-top: 4px;">Low</div>
                    </div>
                </div>
                
                <!-- Horizontal Progress Bar with Markers -->
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <div style="font-size: 0.85em; color: #666; font-weight: 500;">Compliance Progress</div>
                        <div style="font-size: 0.85em; color: #666;">{percentage_str}%</div>
                    </div>
                    <div style="position: relative; height: 24px; background-color: #e9ecef; border-radius: 12px; overflow: hidden; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);">
                        <!-- Progress fill -->
                        <div style="position: absolute; left: 0; top: 0; height: 100%; width: {percentage_val}%; background: linear-gradient(90deg, {gradient_start} 0%, {gradient_end} 100%); border-radius: 12px;"></div>
                        
                        <!-- 50% marker -->
                        <div style="position: absolute; left: 50%; top: 0; height: 100%; width: 2px; background-color: rgba(0,0,0,0.2); z-index: 2;"></div>
                        <div style="position: absolute; left: 50%; top: -18px; transform: translateX(-50%); font-size: 0.7em; color: #666; font-weight: bold; white-space: nowrap;">50%</div>
                        
                        <!-- 75% marker -->
                        <div style="position: absolute; left: 75%; top: 0; height: 100%; width: 2px; background-color: rgba(0,0,0,0.2); z-index: 2;"></div>
                        <div style="position: absolute; left: 75%; top: -18px; transform: translateX(-50%); font-size: 0.7em; color: #666; font-weight: bold; white-space: nowrap;">75%</div>
                    </div>
                </div>
            </div>
            
            <!-- Card Footer with Analysis Info -->
            <div style="background-color: #f8f9fa; padding: 12px 20px; border-top: 1px solid #dee2e6; font-size: 0.85em; color: #666;">
                <i class="fas fa-clock"></i> Analysis: {current_time} UTC · <i class="fas fa-lock"></i> Account: {account_id}
            </div>
        </div>
    </div>
</div>
"""
        return card_html
        
    def buildContentSummary_dashboard(self):
        output = []
        
        # Add health score card at the top
        health_score_card = self.generateHealthScoreCard()
        output.append(health_score_card)
        
        items = []
        dataSets = {
            'S': {'T': 0, 'H': 0, 'M': 0, 'L': 0, 'I': 0},
            'R': {'T': 0, 'H': 0, 'M': 0, 'L': 0, 'I': 0},
            'C': {'T': 0, 'H': 0, 'M': 0, 'L': 0, 'I': 0},
            'P': {'T': 0, 'H': 0, 'M': 0, 'L': 0, 'I': 0},
            'O': {'T': 0, 'H': 0, 'M': 0, 'L': 0, 'I': 0}
        }
        
        hriSets = {
            'H': 0,
            'M': 0,
            'L': 0,
            'I': 0
        }
        
        dashboard = cfg.dashboard.copy()
        
        total = 0
        if not 'CRITICALITY' in dashboard:
            print("0 recommendations detected, expecting empty report")
            return
        
        for region, details in dashboard['CRITICALITY'].items():
            for cat, cnt in details.items():
                if not cat == 'X':
                    hriSets[cat] += cnt
                    
                total += cnt
        
        for cat, count in hriSets.items():
            items.append(self.getHRIInfo(cat, count, total))
        
        for region, details in dashboard['CATEGORY'].items():
            for cat, grp in details.items():
                if cat == 'T':
                    continue
                
                if not cat == 'X':
                    for sev, cnt in grp.items():
                        dataSets[cat][sev] += cnt
                        dataSets[cat]['T'] += cnt
        
        xhtml = "<dl class='row'>" + '\n'.join(items) + "</dl>"
        items = []
        
        pid = self.getHtmlId('criticalityCount')
        card = self.generateCard(pid=pid, html=xhtml, cardClass='danger', title='Findings by Severity Level', titleBadge='', collapse=False, noPadding=False)
        securityBox = self.generateSecurityBigBox(dataSets['S'])
        
        # Add visual separator and label above Security box (Task 2.15)
        customHtml = f"""
<div class="row">
    <div class="col-sm-8">
        {card}
    </div>
    <div class="col-sm-4">
        <!-- Separator with label "Highest Risk Pillar" -->
        <div style="padding-bottom: 10px; margin-bottom: 10px; border-bottom: 2px solid #dc3545; display: flex; align-items: center;">
            <i class="fas fa-exclamation-circle" style="color: #dc3545; margin-right: 8px;"></i>
            <span style="font-weight: 600; color: #333; font-size: 0.95em;">Highest Risk Pillar</span>
        </div>
        {securityBox}
    </div>
</div>
"""
        output.append(customHtml)
        
        for cat, total in dataSets.items():
            if cat == 'S' or cat == 'T':
                continue
            items.append([self.getDashboardCategoryTiles(cat, total), ''])
        
        output.append(self.generateRowWithCol(size=3, items=items, rowHtmlAttr="data-context='pillars'"))
        
        return output
        
    def buildContentDetail_dashboard(self):
        ## Render Top 5 Critical Findings Banner first
        output = []
        top_findings_banner = self.generateTopFindingsBanner()
        output.append(top_findings_banner)
        
        ## Chart - Categorise by Services, Stacked by Region
        items = {}
        serviceLabels = [] 
        regionLabels = []
        donutL = {}
        donutR = {} 
        dataSetsL = {}
        dataSetsR = {}
        filterDonutL = {}
        filterDonutR = {}
        
        regions = self.regions
        services = self.services

        for service, cnt in services.items():
            serviceLabels.append(service)
            dataSetsR[service] = []
            donutR[service] = 0
            
        for region in regions:
            regionLabels.append(region)
            dataSetsL[region] = []
            donutL[region] = 0
            
        dashboard = cfg.dashboard.copy()
            
        for serv, attrs in dashboard['SERV'].items():
            for region in regions:
                hri = cnt = 0
                if region in attrs:
                    cnt = attrs[region]['Total']
                    hri = attrs[region]['H']
                
                dataSetsL[region].append(cnt)
                dataSetsR[serv].append(cnt)
                donutL[region] += hri
                donutR[serv] += hri
        
        for region, cnt in donutL.items():
            if cnt > 0:
                filterDonutL[region] = cnt
        
        for serv, cnt in donutR.items():
            if cnt > 0:
                filterDonutR[serv] = cnt
                
        
        # card = self.generateCard(pid=pid, html=html, cardClass='danger', title='No. Criticality', titleBadge='', collapse=False, noPadding=False)
                
        html = self.generateDonutPieChart(filterDonutL, 'hriByRegion', 'doughnut')
        card = self.generateCard(pid=self.getHtmlId('chartServRegion'), html=html, cardClass='warning', title='Critical Risk Distribution by Region', titleBadge='', collapse=True, noPadding=False)
        items = [[card, '']]
        
        html = self.generateDonutPieChart(filterDonutR, 'hriByService', 'pie')
        card = self.generateCard(pid=self.getHtmlId('pieHriByService'), html=html, cardClass='warning', title='Services with Highest Critical Risk', titleBadge='', collapse=True, noPadding=False)
        items.append([card, ''])
        
        output.append(self.generateRowWithCol(size=6, items=items, rowHtmlAttr="data-context='chartHRICount'"))
        
        items = []
        html = self.generateBarChart(serviceLabels, dataSetsL, 'csr')
        card = self.generateCard(pid=self.getHtmlId('chartServRegion'), html=html, cardClass='info', title='Analysis Coverage by Service', titleBadge='', collapse=True, noPadding=False)
        items.append([card, ''])
        
        html = self.generateBarChart(regionLabels, dataSetsR, 'crs')
        card = self.generateCard(pid=self.getHtmlId('chartRegionServ'), html=html, cardClass='info', title='Analysis Coverage by Region', titleBadge='', collapse=True, noPadding=False)
        items.append([card, ''])
        
        output.append(self.generateRowWithCol(size=6, items=items, rowHtmlAttr="data-context='chartCount'"))
        
        output.append("<h6>Report generated at <u>{}</u>, timezone setting: {}</h6>".format(datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), 'UTC'))
        return output
        
    def getDashboardCategoryTiles(self, key, cnt):
        colorArr = {
            'S': ['danger', 'Security', 'cog'],
            'R': ['fuchsia', 'Reliability', 'globe'],
            'C': ['primary', 'Cost Optimization', 'dollar-sign'],
            'P': ['success', 'Performance Efficiency', 'seedling'],
            'O': ['navy', 'Operation Excellence', 'wrench']
        }
        
        colorClass, title, icon = colorArr[key]
        
        style = "style='color: #dfdfdf'" if key == 'O' else ""
        
        total = cnt['T']
        highCnt = cnt['H']
        mediumCnt = cnt['M']
        lowCnt = cnt['L']
        infoCnt = cnt['I']
        
        # Get description from framework mappings based on pillar
        frameworkDescriptionMap = {
            'S': 'Data protection, identities and threat detection',
            'R': 'Failure recovery and system availability',
            'C': 'Eliminating unnecessary spend and efficient usage',
            'P': 'Optimal use of computing resources',
            'O': 'Operations, monitoring and continuous improvement'
        }
        
        description = frameworkDescriptionMap.get(key, '')
        
        output = f"""
<div class="small-box bg-{colorClass}" style="cursor:pointer;" onClick="window.open('CPFindings.html#{title}', '_blank')">
  <div class="inner">
    <h3>{total}</h3>
    <p>{title}</p>
    <p class="waf-pillar-description" style="font-size: 0.85em; font-weight: normal; color: rgba(255,255,255,0.7); line-height: 1.3; word-wrap: break-word; margin: 8px 0 0 0; padding: 0 2px; overflow-wrap: break-word;">{description}</p>
  </div>
  <div class="icon">
    <i {style} class="fas fa-{icon}"></i>
  </div>
  <div class="row" style="
    background-color: rgba(0,0,0,.1);
    text-align: center;
    margin: 1px;
    ">
    <div class="col-lg-3 col-sm-6"><i class="fas fa-ban"></i> {highCnt}</div>
    <div class="col-lg-3 col-sm-6"><i class="fas fa-exclamation-triangle"></i> {mediumCnt}</div>
    <div class="col-lg-3 col-sm-6"><i class="fas fa-eye"></i> {lowCnt}</div>
    <div class="col-lg-3 col-sm-6"><i class="fas fa-info-circle"></i> {infoCnt}</div>
  </div>
</div>
"""
        return output
        
    def getHRIInfo(self, cat, cnt, total):
        attrArr = {
            'H': ['danger', 'High', 'ban', 'Critical — Immediate action'],
            'M': ['warning', 'Medium', 'exclamation-triangle', 'Moderate — Plan within 30 days'],
            'L': ['info', 'Low', 'eye', 'Low — Review within 90 days'],
            'I': ['primary', 'Informational', 'info-circle', 'Informational — Reference']
        }
        
        colorClass, title, icon, action_label = attrArr[cat]
        
        percentile = round(cnt * 100 / total)
        
        output = f"""
<dt class="col-sm-4"><a style='cursor: pointer; color: black;' target=_blank rel='noopener noreferrer' href='CPFindings.html#{title}'><i class="fas fa-{icon}"></i> {title}</dt></a>
<dd class="col-sm-8" style='text-align: right'>{cnt}</dd>
<dt class="col-sm-12">
<div style="font-size: 11px; color: #6c757d; margin-bottom: 4px; padding-left: 4px;">{action_label}</div>
<div class="progress mb-3">
  <div class="progress-bar bg-{colorClass}" role="progressbar" aria-valuenow="{percentile}" aria-valuemin="0"
	   aria-valuemax="100" style="width: {percentile}%">
	<span>({percentile}%)</span>
  </div>
</div>
</dt>    
"""
        return output
        
    def generateSecurityBigBox(self, cnt):
        total = cnt['T']
        highCnt = cnt['H']
        mediumCnt = cnt['M']
        lowCnt = cnt['L']
        infoCnt = cnt['I']
        
        output = f"""
<div class="small-box bg-danger" style='height: 357px'>
  <div class="inner">
    <h3>{total}</h3>
    <p>Security</p>
    <p class="waf-pillar-description" style="font-size: 0.85em; font-weight: normal; color: rgba(255,255,255,0.7); line-height: 1.3; word-wrap: break-word; margin: 4px 0 0 0; padding: 0 2px;">pillar with the most findings</p>
  </div>
  <div class="icon">
    <i style='color: #dfdfdf' class="fas fa-skull-crossbones"></i>
  </div>
  <div class="row" style="background-color: rgba(0,0,0,.1); text-align: center; font-size:26px; margin: 1px; margin-top: 167px">
    <div class="col-lg-6 col-sm-6"><i class="fas fa-ban"></i> {highCnt}</div>
    <div class="col-lg-6 col-sm-6"><i class="fas fa-exclamation-triangle"></i> {mediumCnt}</div>
    <div class="col-lg-6 col-sm-6"><i class="fas fa-eye"></i> {lowCnt}</div>
    <div class="col-lg-6 col-sm-6"><i class="fas fa-info-circle"></i> {infoCnt}</div>
  </div>
</div>
"""
        return output

    def _getTop5HighFindings(self):
        """
        Extract top 5 services by HIGH severity count from cfg.dashboard['SERV'].
        
        This method aggregates HIGH severity findings across all regions for each service
        and returns the top 5 services sorted by high count in descending order.
        
        Returns:
            list: List of tuples: [(service_name, high_count), ...]
                  Sorted by high_count descending, limited to top 5 services
                  Returns empty list if no HIGH severity findings exist
        
        Example:
            [('IAM', 34), ('EC2', 28), ('S3', 15), ('RDS', 12), ('Lambda', 8)]
        """
        dashboard = cfg.dashboard.copy()
        serv_data = dashboard.get('SERV', {})
        
        # Aggregate HIGH count by service across all regions
        service_high_counts = {}
        
        for service_name, regions_dict in serv_data.items():
            high_count = 0
            
            # Sum HIGH findings across all regions for this service
            for region, region_data in regions_dict.items():
                if isinstance(region_data, dict):
                    high_count += region_data.get('H', 0)
            
            if high_count > 0:
                service_high_counts[service_name] = high_count
        
        # Sort by high_count descending and limit to top 5
        sorted_services = sorted(
            service_high_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_services[:5]

    def generateTopFindingsBanner(self):
        """
        Generate the top 5 critical findings banner with real data from Python.
        
        Displays the top 5 services by HIGH severity count with static HTML
        (no JavaScript-driven data). Each service is listed with its HIGH finding count
        and a link to the service detail page.
        
        Titles and subtitles (English; Spanish scaffolding kept for future i18n):
        - Title: "Immediate Action Priorities"
        - Subtitle: "Services that require priority attention from the technical team"
        
        Format: "[SERVICE_UPPERCASE] — [N critical findings] — [link to {service}.html]"
        
        Collapsible/expandable: Defaults to expanded state with Bootstrap collapse functionality.
        
        Returns:
            str: Static HTML with real service data embedded, CSS, and JavaScript for collapse
        """
        # Get top 5 services by HIGH severity count
        top_services = self._getTop5HighFindings()
        has_findings = len(top_services) > 0
        
        # Generate finding rows for each service
        findings_rows = []
        if has_findings:
            for idx, (service_name, high_count) in enumerate(top_services, 1):
                service_lower = service_name.lower()
                service_page = f"{service_lower}.html"
                
                # Format the text as: "SERVICE — N critical findings — link"
                hallazgos_text = "1 critical finding" if high_count == 1 else f"{high_count} critical findings"
                
                finding_row = f"""
                <div class="finding-item">
                    <div class="finding-rank">{idx}</div>
                    <div class="finding-content">
                        <div class="finding-info">
                            <span class="finding-service">{service_name.upper()}</span>
                            <span class="finding-rule">{hallazgos_text}</span>
                        </div>
                    </div>
                    <div class="finding-button-group">
                        <a href="{service_page}#H" class="btn btn-sm btn-finding-detail" target="_blank" rel="noopener noreferrer">
                            <i class="fas fa-external-link-alt"></i> View details
                        </a>
                    </div>
                </div>
                """
                findings_rows.append(finding_row)
        
        findings_rows_html = "".join(findings_rows)
        findings_count = len(top_services)
        
        # Show/hide sections based on findings
        show_findings_style = "display: block;" if has_findings else "display: none;"
        show_no_findings_style = "display: none;" if has_findings else "display: block;"
        
        # Generate unique IDs for banner and collapse target
        banner_id = "top-findings-banner"
        content_id = f"{banner_id}-content-collapse"
        
        # Build static HTML banner with Bootstrap collapse functionality
        banner_html = f"""
        <div class="row" id="{banner_id}-row" style="margin-top: 20px; margin-bottom: 20px;">
            <div class="col-12">
                <!-- Alert Card with Top 5 Services -->
                <div class="alert alert-danger alert-dismissible fade show" id="{banner_id}" role="alert" style="border-left: 4px solid #dc3545; box-shadow: 0 2px 4px rgba(220,53,69,0.1); margin-bottom: 0;">
                    <!-- Header with icon, title, and collapse toggle -->
                    <div class="alert-header" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px; padding-bottom: 12px; border-bottom: 1px solid rgba(220,53,69,0.2);">
                        <div style="display: flex; align-items: center; flex-grow: 1;">
                            <i class="icon fas fa-fire" style="font-size: 1.3em; margin-right: 10px; color: #dc3545;"></i>
                            <div style="flex-grow: 1;">
                                <h5 style="margin: 0 0 4px 0; font-weight: bold; color: #721c24;">
                                    Immediate Action Priorities
                                </h5>
                                <p style="margin: 0; font-size: 0.85em; color: #721c24; font-weight: 500;">
                                    Services that require priority attention from the technical team
                                </p>
                            </div>
                        </div>
                        <div style="display: flex; gap: 8px; align-items: center; flex-shrink: 0;">
                            <!-- Collapse toggle button -->
                            <button class="btn btn-sm btn-link-collapse" type="button" data-toggle="collapse" data-target="#{content_id}" 
                                    aria-expanded="true" aria-controls="{content_id}" style="color: #721c24; text-decoration: none; padding: 0; font-size: 1.2em;">
                                <i class="fas fa-chevron-up" style="transition: transform 0.3s ease;"></i>
                            </button>
                            <!-- Dismiss button -->
                            <button type="button" class="close" data-dismiss="alert" aria-label="Close" style="color: #721c24; margin: 0; padding: 0; font-size: 1.5em;">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                    </div>

                    <!-- Success message (shown when no findings) -->
                    <div id="{banner_id}-empty" style="{show_no_findings_style}">
                        <div style="text-align: center; padding: 20px;">
                            <i class="fas fa-check-circle" style="font-size: 2em; color: #28a745; margin-bottom: 10px;"></i>
                            <p style="color: #155724; margin: 10px 0 0 0;">
                                <strong>Great news!</strong> No critical findings were detected in this assessment.
                            </p>
                        </div>
                    </div>

                    <!-- Findings list (collapsible, static HTML with real data) -->
                    <div class="collapse show" id="{content_id}">
                        <div id="{banner_id}-content" style="{show_findings_style}">
                            <div class="findings-container" style="background-color: rgba(220,53,69,0.03); border-radius: 4px; padding: 0;">
                                {findings_rows_html}
                            </div>
                            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(220,53,69,0.1);">
                                <small style="color: #721c24;">
                                    <i class="fas fa-info-circle"></i>
                                    <strong>Showing the top {findings_count} services with critical findings.</strong>
                                    Review the service detail pages for additional findings.
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
        
        # Add CSS for styling
        css_code = """
        <style>
            /* Finding item row styles */
            .finding-item {{
                display: flex;
                align-items: flex-start;
                padding: 12px;
                border-bottom: 1px solid rgba(220,53,69,0.15);
                background-color: transparent;
                transition: background-color 0.2s ease;
            }}

            .finding-item:last-child {{
                border-bottom: none;
            }}

            .finding-item:hover {{
                background-color: rgba(220,53,69,0.08);
            }}

            /* Finding rank/number badge */
            .finding-rank {{
                display: flex;
                align-items: center;
                justify-content: center;
                width: 32px;
                height: 32px;
                background-color: #dc3545;
                color: white;
                border-radius: 50%;
                font-weight: bold;
                font-size: 0.95em;
                margin-right: 12px;
                flex-shrink: 0;
            }}

            /* Finding content container */
            .finding-content {{
                flex-grow: 1;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}

            /* Finding service and severity info */
            .finding-info {{
                display: flex;
                flex-direction: column;
                gap: 4px;
                margin-bottom: 6px;
            }}

            .finding-service {{
                font-weight: 600;
                color: #721c24;
                font-size: 0.95em;
            }}

            .finding-rule {{
                color: #333;
                font-size: 0.9em;
                word-break: break-word;
            }}

            /* "Ver detalles" button */
            .finding-button-group {{
                display: flex;
                gap: 8px;
                margin-left: 12px;
                flex-shrink: 0;
            }}

            .btn-finding-detail {{
                padding: 6px 12px;
                font-size: 0.85em;
                font-weight: 500;
                background-color: #dc3545;
                border-color: #dc3545;
                color: white;
                white-space: nowrap;
                transition: all 0.2s ease;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }}

            .btn-finding-detail:hover {{
                background-color: #c82333;
                border-color: #bd2130;
                color: white;
                text-decoration: none;
            }}

            .btn-finding-detail:focus {{
                outline: 2px solid #dc3545;
                outline-offset: 2px;
            }}

            /* Collapse toggle button */
            .btn-link-collapse {{
                padding: 0 !important;
                margin: 0 !important;
                background: none !important;
                border: none !important;
            }}

            .btn-link-collapse:hover {{
                color: #5a1419 !important;
            }}

            .btn-link-collapse[aria-expanded="false"] i {{
                transform: rotate(180deg);
            }}

            /* Collapse animation */
            .collapse {{
                overflow: hidden;
                transition: max-height 0.3s ease, opacity 0.3s ease;
            }}

            .collapse:not(.show) {{
                display: none;
            }}

            .collapse.show {{
                display: block;
            }}

            /* Responsive adjustments */
            @media (max-width: 768px) {{
                .finding-item {{
                    flex-direction: column;
                    padding: 10px;
                }}

                .finding-rank {{
                    width: 28px;
                    height: 28px;
                    font-size: 0.85em;
                    margin-right: 8px;
                    margin-bottom: 0;
                }}

                .finding-content {{
                    width: 100%;
                }}

                .finding-button-group {{
                    margin-left: 0;
                    margin-top: 8px;
                    width: 100%;
                }}

                .btn-finding-detail {{
                    flex: 1;
                    text-align: center;
                    justify-content: center;
                }}
            }}

            /* Alert animation */
            .alert-danger {{
                animation: slideDown 0.3s ease-out;
            }}

            @keyframes slideDown {{
                from {{
                    opacity: 0;
                    transform: translateY(-10px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
        </style>
        """
        
        # Add JavaScript for enhanced collapse functionality
        js_code = """
        <script>
            (function() {{
                // Initialize collapse toggle icon rotation
                document.addEventListener('DOMContentLoaded', function() {{
                    const collapseBtn = document.querySelector('[data-toggle="collapse"][data-target="#top-findings-banner-content-collapse"]');
                    const collapseTarget = document.querySelector('#top-findings-banner-content-collapse');
                    
                    if (!collapseBtn || !collapseTarget) return;
                    
                    // Update icon rotation based on collapse state
                    function updateIconRotation() {{
                        const icon = collapseBtn.querySelector('i');
                        const isExpanded = collapseTarget.classList.contains('show');
                        collapseBtn.setAttribute('aria-expanded', isExpanded);
                    }}
                    
                    // Listen for Bootstrap collapse events
                    collapseTarget.addEventListener('hide.bs.collapse', function() {{
                        updateIconRotation();
                    }});
                    
                    collapseTarget.addEventListener('show.bs.collapse', function() {{
                        updateIconRotation();
                    }});
                    
                    // Initial state
                    updateIconRotation();
                }});
            }})();
        </script>
        """
        
        return banner_html + css_code + js_code
    
    def _escape_html(self, text):
        """Escape HTML special characters in text for safe rendering"""
        if not isinstance(text, str):
            return str(text)
        
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;'
        }
        
        for char, escape in replacements.items():
            text = text.replace(char, escape)
        
        return text
    
    def _get_fallback_banner_template(self):
        """Fallback template if file not found"""
        return """
        <div class="row" id="top-findings-banner-row" style="margin-top: 20px; margin-bottom: 20px;">
            <div class="col-12">
                <div class="alert alert-danger alert-dismissible fade show" id="top-findings-alert" role="alert" style="border-left: 4px solid #dc3545;">
                    <div class="alert-header" style="display: flex; align-items: center; margin-bottom: 15px; padding-bottom: 12px; border-bottom: 1px solid rgba(220,53,69,0.2);">
                        <i class="icon fas fa-fire" style="font-size: 1.3em; margin-right: 10px;"></i>
                        <h5 style="margin: 0; font-weight: bold;">Top 5 Critical Findings</h5>
                        <button type="button" class="close" data-dismiss="alert">&times;</button>
                    </div>
                    <div id="top-findings-empty" style="{$SHOW_NO_FINDINGS}">
                        <p style="color: #155724;">No high-severity findings detected.</p>
                    </div>
                    <div id="top-findings-list" style="display:none;">{$TOP_FINDINGS_ROWS}</div>
                </div>
            </div>
        </div>
        """