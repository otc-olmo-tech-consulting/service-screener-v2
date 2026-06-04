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
        Generate the health score card HTML.
        
        Retrieves health score from cfg.dashboard and renders it as a prominent card
        positioned above WAF pillar tiles. Uses template variables for percentage, grade,
        and color injection.
        
        Returns:
            str: HTML for health score card with template variables injected
        """
        dashboard = cfg.dashboard.copy()
        health_score = dashboard.get('HEALTH_SCORE', {})
        
        # Extract health score values with defaults
        percentage = health_score.get('percentage', 100)
        grade = health_score.get('grade', 'A').upper()
        raw_score = health_score.get('raw_score', 0)
        
        # Format percentage with 1 decimal place as per requirement
        if isinstance(percentage, (int, float)):
            percentage_str = f"{percentage:.1f}"
        else:
            percentage_str = "100.0"
        
        # Map grade to Bootstrap color class and status label
        color_class, status_label = self.get_health_color_and_status(grade)
        
        # Build health score card with template variables
        # {$HEALTH_PERCENTAGE}, {$HEALTH_GRADE}, {$HEALTH_COLOR}
        card_html = f"""
<div class="row" style="margin-bottom: 20px;">
    <div class="col-md-12">
        <div class="card bg-gradient-{color_class}" style="border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div class="card-body" style="padding: 30px;">
                <div class="row" style="align-items: center;">
                    <div class="col-md-4">
                        <h5 style="margin: 0; font-weight: bold; color: rgba(255,255,255,0.9);">Health Score</h5>
                    </div>
                    <div class="col-md-8" style="text-align: right;">
                        <div style="font-size: 2.5em; font-weight: bold; margin: 0; color: rgba(255,255,255,1);">{percentage_str}%</div>
                        <div style="font-size: 1.1em; margin-top: 5px; margin-bottom: 5px; color: rgba(255,255,255,0.95);">Grade <span style="font-weight: bold;">{grade}</span></div>
                        <div style="font-size: 0.9em; color: rgba(255,255,255,0.85);">{status_label}</div>
                    </div>
                </div>
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
        card = self.generateCard(pid=pid, html=xhtml, cardClass='danger', title='No. Criticality', titleBadge='', collapse=False, noPadding=False)
        securityBox = self.generateSecurityBigBox(dataSets['S'])
        
        customHtml = f"""
<div class="row">
    <div class="col-sm-8">
        {card}
    </div>
    {securityBox}
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
        card = self.generateCard(pid=self.getHtmlId('chartServRegion'), html=html, cardClass='warning', title='High Risk - Group by Region', titleBadge='', collapse=True, noPadding=False)
        items = [[card, '']]
        
        html = self.generateDonutPieChart(filterDonutR, 'hriByService', 'pie')
        card = self.generateCard(pid=self.getHtmlId('pieHriByService'), html=html, cardClass='warning', title='High Risk - Group by Service', titleBadge='', collapse=True, noPadding=False)
        items.append([card, ''])
        
        output.append(self.generateRowWithCol(size=6, items=items, rowHtmlAttr="data-context='chartHRICount'"))
        
        items = []
        html = self.generateBarChart(serviceLabels, dataSetsL, 'csr')
        card = self.generateCard(pid=self.getHtmlId('chartServRegion'), html=html, cardClass='info', title='Chart by Serv by Region', titleBadge='', collapse=True, noPadding=False)
        items.append([card, ''])
        
        html = self.generateBarChart(regionLabels, dataSetsR, 'crs')
        card = self.generateCard(pid=self.getHtmlId('chartRegionServ'), html=html, cardClass='info', title='Chart by Region by Serv', titleBadge='', collapse=True, noPadding=False)
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
            'S': 'Protección de datos, identidades y detección de amenazas',
            'R': 'Recuperación ante fallos y disponibilidad del sistema',
            'C': 'Eliminación de gastos innecesarios y uso eficiente',
            'P': 'Uso óptimo de recursos computacionales',
            'O': 'Operaciones, monitoreo y mejora continua'
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
            'H': ['danger', 'High', 'ban'],
            'M': ['warning', 'Medium', 'exclamation-triangle'],
            'L': ['info', 'Low', 'eye'],
            'I': ['primary', 'Informational', 'info-circle']
        }
        
        colorClass, title, icon = attrArr[cat]
        
        percentile = round(cnt * 100 / total)
        
        output = f"""
<dt class="col-sm-4"><a style='cursor: pointer; color: black;' target=_blank rel='noopener noreferrer' href='CPFindings.html#{title}'><i class="fas fa-{icon}"></i> {title}</dt></a>
<dd class="col-sm-8" style='text-align: right'>{cnt}</dd>
<dt class="col-sm-12">
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
<div class="col-sm-4" style="cursor:pointer;" onClick="window.open('CPFindings.html#Security', '_blank')">
	<div class="small-box bg-danger" style='height: 357px'>
	  <div class="inner">
		<h3>{total}</h3>
		<p>Security</p>
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
</div>
"""
        return output

    def generateTopFindingsBanner(self):
        """
        Generate the top 5 critical findings banner HTML.
        
        Retrieves top findings from cfg.dashboard and renders them as an alert card
        with collapsible header and finding item rows.
        
        Returns:
            str: HTML for top 5 findings banner with template variables injected
        """
        dashboard = cfg.dashboard.copy()
        top_findings = dashboard.get('TOP_FINDINGS', [])
        
        # Determine if we have findings
        has_findings = len(top_findings) > 0
        show_no_findings_style = "" if has_findings else "display:none;"
        show_findings_display = "none" if not has_findings else ""
        
        # Generate finding rows
        findings_rows = []
        if has_findings:
            for idx, finding in enumerate(top_findings[:5], 1):
                service = finding.get('service', 'Unknown').lower()
                rule = finding.get('rule', 'unknown_rule')
                description = finding.get('description', 'No description available')
                affected_resources = finding.get('affected_resources', 0)
                
                # Generate the service page link with rule anchor
                service_page = f"{service}.html"
                rule_anchor = rule.replace('_', '-')  # Standardize anchor format
                link_href = f"{service_page}#{rule_anchor}"
                
                # Format resource count text
                resource_text = "1 resource affected" if affected_resources == 1 else f"{affected_resources} resources affected"
                
                # Escape HTML in description
                description_safe = self._escape_html(description)
                
                finding_row = f"""
                <div class="finding-item">
                    <div class="finding-rank">{idx}</div>
                    <div class="finding-content">
                        <div class="finding-info">
                            <span class="finding-service">{service}</span>
                            <span class="finding-rule">{rule}</span>
                        </div>
                        <div class="finding-description">
                            {description_safe}
                        </div>
                        <div class="finding-metadata">
                            <div class="finding-resources">
                                <i class="fas fa-server"></i>
                                <span>{resource_text}</span>
                            </div>
                        </div>
                    </div>
                    <div class="finding-button-group">
                        <a href="{link_href}" class="btn btn-sm btn-finding-detail" target="_blank" rel="noopener noreferrer">
                            <i class="fas fa-external-link-alt"></i> Ver detalle
                        </a>
                    </div>
                </div>
                """
                findings_rows.append(finding_row)
        
        findings_rows_html = "".join(findings_rows)
        findings_count = len(top_findings[:5])
        
        # Load template
        try:
            template_path = 'services/dashboard/top_findings_banner.template.html'
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except (FileNotFoundError, IOError):
            # Fallback if template file not found
            template = self._get_fallback_banner_template()
        
        # Replace template variables
        banner_html = template.replace('{$TOP_FINDINGS_COUNT}', str(findings_count))
        banner_html = banner_html.replace('{$TOP_FINDINGS_ROWS}', findings_rows_html)
        banner_html = banner_html.replace('{$SHOW_NO_FINDINGS}', show_no_findings_style)
        
        # Add JavaScript to handle empty findings display
        js_code = f"""
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                var hasFindings = {str(has_findings).lower()};
                var emptyDiv = document.getElementById('top-findings-empty');
                var listDiv = document.getElementById('top-findings-list');
                
                if (hasFindings) {{
                    if (emptyDiv) emptyDiv.style.display = 'none';
                    if (listDiv) listDiv.style.display = 'block';
                }} else {{
                    if (emptyDiv) emptyDiv.style.display = 'block';
                    if (listDiv) listDiv.style.display = 'none';
                }}
            }});
        </script>
        """
        
        return banner_html + js_code
    
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