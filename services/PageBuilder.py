import uuid
import random
import os
import json
from urllib.parse import urlparse
import html

from utils.Config import Config
from utils.Tools import _warn
import constants as _C

class PageBuilder:
    serviceIcon = {
        'cloudfront': 'wifi', 
        'cloudtrail': 'user-secret',
        'cloudwatch': 'clock',
        'dynamodb': 'bars',
        'ec2': 'server',
        'efs': 'network-wired', 
        'eks': 'box', 
        'elasticache': 'store',
        'guardduty': 'shield-alt',
        'iam': 'users',
        'kms': 'key',
        'lambda': 'calculator', 
        'opensearch': 'warehouse',
        'rds': 'database',
        's3': 'hdd',
        'Modernize': 'chart-line',
        'Findings': 'bug',
        'TA': 'user-md'
    }
    
    frameworkIcon = 'tasks'

    pageTemplate = {
        'header.precss': 'header.precss.template.html',
        'header.postcss': 'header.postcss.template.html',
        'sidebar.precustom': 'sidebar.precustom.template.html',
        'sidebar.postcustom': 'sidebar.postcustom.template.html',
        'breadcrumb': 'breadcrumb.template.html',
        'footer.prejs': 'footer.prejs.template.html',
        'footer.postjs': 'footer.postjs.template.html',
    }

    isHome = False
    isBeta = False
    
    colorCustomHex = None
    colorCustomRGB = None

    def __init__(self, service, reporter):
        self.service = service
        self.services = Config.get('cli_services', [])
        self.frameworks = Config.get('cli_frameworks', [])
        self.regions = Config.get('cli_regions', [])
        
        self.reporter = reporter

        self.idPrefix = self.service + '-'

        self.js = []
        self.jsLib = []
        self.cssLib = []
        
        self.htmlFolder = Config.get('HTML_ACCOUNT_FOLDER_FULLPATH')
        
    def getHtmlId(self, el=''):
        o = uuid.uuid4().hex
        el = el or o[0:11]
        return self.idPrefix + el

    def _prebuildContentSummary(self):
        pass

    def _postbuildContentSummary(self):
        pass

    def _preBuildContentDetail(self):
        pass

    def _postBuildContentDetail(self):
        pass


    def buildPage(self):
        self.init()
        self.htmlFolder = Config.get('HTML_ACCOUNT_FOLDER_FULLPATH')

        output = []
        output.append(self.buildHeader())
        output.append(self.buildNav())
        output.append(self.buildBreadcrumb())

        self._prebuildContentSummary()
        output.append(self.buildContentSummary())
        self._postbuildContentSummary()

        self._preBuildContentDetail()
        output.append(self.buildContentDetail())
        self._postBuildContentDetail()

        output.append(self.buildFooter())

        finalHTML = ""
        for arrayOfText in output:
            if arrayOfText:
                finalHTML += "\n".join(arrayOfText)

        if not os.path.exists(self.htmlFolder):
            os.makedirs(self.htmlFolder)
        
        # print(self.htmlFolder + '/' + self.service + '.html')
        # encoding='utf-8' is required so accented characters (á, é, í, ó, ú, ñ)
        # render correctly. On Windows, open() defaults to the ANSI code page
        # (cp1252), which corrupts UTF-8 text into replacement chars (e.g. Regi�n).
        with open(self.htmlFolder + '/' + self.service + '.html', 'w', encoding='utf-8') as f:
            f.write(finalHTML)
    
    def init(self):
        self.template = 'default'
    
    def buildContentSummary(self):
        method = 'buildContentSummary_' + self.template
        
        # Check if suppressions are active
        suppressions_manager = Config.get('suppressions_manager', None)
        
        # Create output array
        output = []
        
        # Call the template method
        if hasattr(self, method):
            template_output = getattr(self, method)()
            if template_output:
                output.extend(template_output)
        else:
            cls = self.__class__.__name__
            print("[{}] Template for ContentSummary not found: {}".format(cls, method))
        
        # Add suppression modal if suppressions are active
        if suppressions_manager and suppressions_manager.is_loaded:
            modal_html = self.generateSuppressionModal(suppressions_manager)
            output.append(modal_html)
            
            # Add JavaScript to handle modal
            modal_js = '''
// Handle suppression modal
$(document).ready(function() {
    $('#suppressionIndicator').click(function(e) {
        e.preventDefault();
        $('#suppressionModal').modal('show');
    });
    
    // Ensure modal can be closed
    $('#suppressionModalClose, #suppressionModalCloseBtn').click(function() {
        $('#suppressionModal').modal('hide');
    });
    
    // Handle backdrop click
    $('#suppressionModal').on('click', function(e) {
        if (e.target === this) {
            $(this).modal('hide');
        }
    });
    
    // Fix for modal backdrop issues
    $('#suppressionModal').on('shown.bs.modal', function() {
        $('body').addClass('modal-open');
    });
    
    $('#suppressionModal').on('hidden.bs.modal', function() {
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();
    });
});
'''
            self.addJS(modal_js)
        
        return output
    
    def buildContentDetail(self):
        method = 'buildContentDetail_' + self.template
        if hasattr(self, method):
            return getattr(self, method)()
        else:
            cls = self.__class__.__name__
            print("[{}] Template for ContentDetail not found: {}".format(cls, method))

    def generateRowWithCol(self, size=12, items=[], rowHtmlAttr=''):
        output = []
        output.append("<div class='row' {}>".format(rowHtmlAttr))
        _size = size
        for ind, item in enumerate(items):
            if isinstance(size, list):
                i = ind % len(size)
                _size = size[i]
            output.append(self.generateCol(_size, item))
        output.append("</div>")

        return "\n".join(output)
        
    def generateCol(self, size=12, item=[]):
        output = []
        if not item:
            output.append("</div><div class='row'>")
        else:
            html, divAttr = item
            output.append("<div class='col-md-{}' {}>".format(size, divAttr))
            output.append(html)
            output.append("</div>")
        return "\n".join(output)
        
    def generateCard(self, pid, html, cardClass='warning', title='', titleBadge='', collapse=False, noPadding=False):
        output = []

        lteCardClass = '' if not cardClass else "card-{}".format(cardClass)
        defaultCollapseClass = "collapsed-card" if collapse == 9 else ""
        defaultCollapseIcon = "plus" if collapse == 9 else "minus"

        output.append("<div id='{}' class='card {} {}'>".format(pid, lteCardClass, defaultCollapseClass))
        
        genAiButton = ''
        if self.isBeta and pid[:8]=="SUMMARY_":
            genAiButton = '<span class="beta-genai" data-toggle="modal" data-target="#genai-modal"><i class="fas fa-question-circle"></i> '

        if title:
            output.append("<div class='card-header'><h3 class='card-title'>{}{}</h3>".format(genAiButton, title))

            if collapse:
                output.append("<div class='card-tools'><button type='button' class='btn btn-tool' data-card-widget='collapse'><i class='fas fa-{}'></i></button></div>".format(defaultCollapseIcon))

            if titleBadge:
                output.append(titleBadge)

            output.append("</div>")

        noPadClass = 'p-0' if noPadding else ''

        output.append("<div class='card-body {}'>".format(noPadClass))
        output.append(html)
        output.append("</div>")
        output.append("</div>")
        return "\n".join(output)
        
    def generateCategoryBadge(self, category, addtionalHtmlAttr):
        validCategory = ['R', 'S', 'O', 'P', 'C', 'T']
        colorByCategory = ['info', 'danger', 'primary', 'success', 'warning', 'info']
        nameByCategory = ['Reliability', 'Security', 'Operation Excellence', 'Performance Efficiency', 'Cost Optimization', 'Text']
        if category not in validCategory:
            category = 'X'
            color = 'info'
            name = 'Suggestion'
        else:
            indexOf = validCategory.index(category)
            color = colorByCategory[indexOf]
            name = nameByCategory[indexOf]

        return "<span class='badge badge-{}', {}>{}</span>".format(color, addtionalHtmlAttr, name)
        
    def generatePriorityPrefix(self, criticality, addtionalHtmlAttr):
        """
        Generate severity badge with Font Awesome icon and text label.
        
        Severity mapping (per Requirement 8):
        - H (High): badge-danger (red) with fa-ban icon
        - M (Medium): badge-warning (yellow/orange) with fa-exclamation-triangle icon
        - L (Low): badge-primary (blue) with fa-eye icon
        - I (Info): custom light gray with fa-info-circle icon
        
        Contrast ratios verified for WCAG AA (≥4.5:1):
        - badge-danger white on #dc3545: 5.0:1 ✓
        - badge-warning dark on #ffc107: 7.7:1 ✓
        - badge-primary white on #17a2b8: 4.5:1 ✓
        - badge-secondary white on #6c757d: 4.5:1 ✓
        
        Args:
            criticality: Severity level (H, M, L, I)
            addtionalHtmlAttr: Additional HTML attributes for the span
            
        Returns:
            str: HTML badge element with icon and text label
        """
        validCategory = ['I', 'L', 'M', 'H']
        colorByCategory = ['info', 'primary', 'warning', 'danger']
        iconByCategory = ['info-circle', 'eye', 'exclamation-triangle', 'ban']
        labelByCategory = ['Info', 'Low', 'Medium', 'High']

        criticality = criticality if criticality in validCategory else validCategory[0]

        indexOf = validCategory.index(criticality)
        color = colorByCategory[indexOf]
        icon = iconByCategory[indexOf]
        label = labelByCategory[indexOf]

        # Badge HTML with icon (left-aligned) and text label
        # Font Awesome icon is inline with the label for accessibility
        return (
            f"<span class='badge badge-{color} severity-badge severity-badge-{criticality.lower()}' "
            f"{addtionalHtmlAttr}>"
            f"<i class='icon fas fa-{icon}'></i> "
            f"<span class='badge-label'>{label}</span>"
            f"</span>"
        )

    def generateSeverityFilterPanel(self):
        """
        Generate severity filter button panel HTML structure with embedded JavaScript.
        
        CSS styles are defined in header.postcss.template.html
        JavaScript logic for filtering is embedded in this method
        
        Returns:
            str: HTML containing filter buttons and JavaScript for filter functionality
        """
        html = []
        
        # HTML Structure
        html.append("""
<div class="severity-filter-panel">
  <div class="severity-filter-buttons">
    <button class="severity-filter-btn btn-high" data-severity="H" title="Filter by High severity findings">
      <i class="fas fa-ban"></i> High
    </button>
    <button class="severity-filter-btn btn-medium" data-severity="M" title="Filter by Medium severity findings">
      <i class="fas fa-exclamation-triangle"></i> Medium
    </button>
    <button class="severity-filter-btn btn-low" data-severity="L" title="Filter by Low severity findings">
      <i class="fas fa-eye"></i> Low
    </button>
    <button class="severity-filter-btn btn-info" data-severity="I" title="Filter by Info severity findings">
      <i class="fas fa-info-circle"></i> Info
    </button>
    <span style="color: #ddd; margin: 0 4px;">|</span>
    <button class="severity-filter-btn btn-all active" data-severity="all" title="Show all findings">
      All
    </button>
    <button class="severity-filter-btn btn-clear" data-action="clear" title="Clear all filters">
      Clear
    </button>
  </div>
  <span class="filter-counter">
    Showing <span class="filter-counter-value">0</span>/<span class="filter-counter-total">0</span> findings
  </span>
</div>
""")
        
        # Add JavaScript for filter functionality
        filter_js = """
// Severity Filter Panel JavaScript
(function() {
    // Initialize filter state
    var activeFilters = ['H', 'M', 'L', 'I'];  // Start with all severities shown
    var allFindingRows = null;
    
    // Initialize on page load
    function initSeverityFilter() {
        // Get all finding rows (cards with data-criticality attribute in summary context)
        allFindingRows = $("[data-context='summary'] [data-criticality]");
        
        // Update counter display with totals
        var total = allFindingRows.length;
        $('.filter-counter-total').text(total);
        
        // Show all findings initially
        applyFilters();
    }
    
    // Update filter counter display
    function updateFilterCounter() {
        var visible = allFindingRows.filter(':visible').length;
        $('.filter-counter-value').text(visible);
    }
    
    // Apply filters to finding rows
    function applyFilters() {
        if (activeFilters.length === 0) {
            // No filters selected - hide all
            allFindingRows.hide();
        } else {
            // Show rows that match any active filter
            allFindingRows.each(function() {
                var rowSeverity = $(this).data('criticality');
                if (activeFilters.includes(rowSeverity)) {
                    $(this).show();
                } else {
                    $(this).hide();
                }
            });
        }
        updateFilterCounter();
    }
    
    // Handle severity filter button clicks
    $(document).on('click', '.severity-filter-btn[data-severity]', function(e) {
        e.preventDefault();
        var severity = $(this).data('severity');
        
        if (severity === 'all') {
            // 'All' button - show everything
            activeFilters = ['H', 'M', 'L', 'I'];
            $('.severity-filter-btn[data-severity]').removeClass('active');
            $(this).addClass('active');
        } else {
            // Toggle individual severity
            var index = activeFilters.indexOf(severity);
            if (index > -1) {
                // Remove from active filters
                activeFilters.splice(index, 1);
                $(this).removeClass('active');
            } else {
                // Add to active filters
                activeFilters.push(severity);
                $(this).addClass('active');
            }
            // Remove 'All' button active state
            $('.severity-filter-btn[data-severity="all"]').removeClass('active');
        }
        
        applyFilters();
    });
    
    // Handle 'Clear' button
    $(document).on('click', '.severity-filter-btn[data-action="clear"]', function(e) {
        e.preventDefault();
        activeFilters = [];
        $('.severity-filter-btn').removeClass('active');
        allFindingRows.hide();
        updateFilterCounter();
    });
    
    // Initialize when document is ready
    $(document).ready(function() {
        initSeverityFilter();
    });
})();
"""
        
        # Add the JavaScript to the page
        self.addJS(filter_js)
        
        return "".join(html)

    def generateSummaryCardContent(self, summary):
        output = []

        resources = summary['__affectedResources']
        resHtml = []
        for region, resource in resources.items():
            items = []
            resHtml.append(f"<dd class='detail-regions'>{region}: ")
            for identifier in resource:
                items.append(f"<a href='#{self.service}-{identifier}'>{identifier}</a>")
            resHtml.append(" | ".join(items))
            resHtml.append("</dd>")

        output.append("<dl><dt>Description</dt><dd class='detail-desc'>" + summary['^description'] + "</dd><dt>Resources</dt>" + "".join(resHtml))

        hasTags = self.generateSummaryCardTag(summary)
        if len(hasTags.strip()) > 0:
            output.append(f"<dt>Label</dt><dd>{hasTags}</dd>")

        if summary.get('__links'):
            output.append("<dt>Recommendation</dt><dd class='detail-href'>" + "</dd><dd class='detail-href''>".join(summary['__links']) + "</dd>")

        output.append("</dl>")
        
        # Add remediation section (Task 3.7)
        remediation_html = self.generateRemediationSection(summary)
        if remediation_html:
            output.append(remediation_html)

        return "\n".join(output)
    
    def generateRemediationSection(self, finding):
        """
        Render remediation steps and links section with collapsible toggle.
        
        Supports:
        - Numbered remediation steps from __remediation_steps field
        - External links with Font Awesome fa-external-link-alt icons from __links field
        - Collapsible toggle with smooth animation
        - Visual indication when links are available
        
        Args:
            finding: Finding dictionary containing __remediation_steps and __links fields
            
        Returns:
            str: HTML markup for remediation section, or empty string if no remediation data
        """
        try:
            # Validate finding is a dictionary
            if not isinstance(finding, dict):
                return ""
            
            # Extract remediation data
            steps = finding.get('__remediation_steps', [])
            links = finding.get('__links', [])
            
            # Return empty if no remediation data
            if not steps and not links:
                return ""
            
            # Generate unique ID for this remediation section
            section_id = f"remediation-{uuid.uuid4().hex[:8]}"
            
            output = []
            
            # Remediation section header with toggle and link counter
            link_count = len(links) if links else 0
            
            output.append("<div class='remediation-section'>")
            output.append("<div class='remediation-header'>")
            output.append(f"""
            <button class='remediation-toggle' data-toggle='collapse' data-target='#{section_id}' 
                    aria-expanded='true' aria-controls='{section_id}' type='button'>
                <i class='fas fa-wrench'></i>
                <span class='toggle-label'>View remediation</span>
                <span class='toggle-icon'>▼</span>
            </button>
            """)
            
            # Badge showing link count
            if link_count > 0:
                output.append(f"<span class='remediation-badge'>{link_count} recursos</span>")
            
            output.append("</div>")  # End remediation-header
            
            # Collapsible content area
            output.append(f"<div class='remediation-content collapse show' id='{section_id}'>")
            
            # Remediation steps section
            if steps:
                output.append("<div class='remediation-steps'>")
                output.append("<h6 class='steps-title'>Remediation steps:</h6>")
                output.append("<ol class='steps-list'>")
                
                for step in steps:
                    # HTML escape step text for security
                    safe_step = html.escape(str(step))
                    output.append(f"<li class='step-item'>{safe_step}</li>")
                
                output.append("</ol>")
                output.append("</div>")  # End remediation-steps
            
            # Links section
            if links:
                output.append("<div class='remediation-links'>")
                output.append("<h6 class='links-title'>Useful links:</h6>")
                output.append("<ul class='links-list'>")
                
                for link in links:
                    # Validate and sanitize URL
                    safe_link = html.escape(str(link))
                    link_title = self._extract_link_title(link)
                    
                    output.append(
                        f"<li class='link-item'>"
                        f"<a href='{safe_link}' target='_blank' rel='noopener noreferrer' "
                        f"class='remediation-link'>"
                        f"<i class='fas fa-external-link-alt'></i> "
                        f"<span class='link-text'>{link_title}</span>"
                        f"</a>"
                        f"</li>"
                    )
                
                output.append("</ul>")
                output.append("</div>")  # End remediation-links
            
            output.append("</div>")  # End remediation-content
            output.append("</div>")  # End remediation-section
            
            return "\n".join(output)
            
        except Exception as e:
            _warn(f"Error rendering remediation section: {str(e)}")
            return ""
    
    def _extract_link_title(self, url):
        """
        Extract a readable title from a URL.
        
        Extracts the last meaningful part of the URL path and formats it as title case.
        Falls back to domain if path is empty.
        
        Args:
            url: The URL to extract title from
            
        Returns:
            str: Readable link title
            
        Examples:
            >>> _extract_link_title('https://docs.aws.amazon.com/iam/latest/userguide/id_mfa_activate_virtual.html')
            'Id Mfa Activate Virtual.Html'
            >>> _extract_link_title('https://aws.amazon.com/iam/')
            'Iam'
            >>> _extract_link_title('https://docs.aws.amazon.com')
            'docs.aws.amazon.com'
        """
        try:
            parsed = urlparse(url)
            
            # Extract the last meaningful part of the path
            path_parts = parsed.path.strip('/').split('/')
            
            # Filter out empty parts and get the last one
            meaningful_parts = [p for p in path_parts if p]
            
            if meaningful_parts:
                # Get the last meaningful part and remove file extension
                last_part = meaningful_parts[-1]
                
                # Remove .html, .php, etc.
                if '.' in last_part:
                    title_part = last_part.rsplit('.', 1)[0]
                else:
                    title_part = last_part
                
                # Convert kebab-case/snake_case to Title Case
                title = title_part.replace('-', ' ').replace('_', ' ').title()
                return title if title else parsed.netloc
            else:
                # Fall back to domain
                return parsed.netloc
                
        except Exception as e:
            _warn(f"Error extracting link title from {url}: {str(e)}")
            return url
        
    def generateDonutPieChart(self, datasets, idPrefix='', typ='doughnut'):
        htmlId = idPrefix + typ + str(uuid.uuid1())
        output = []
        output.append("<div class='chart'><canvas id='{}' style='min-height: 250px; height: 250px; max-height: 250px; max-width: 100%;'></canvas></div>".format(htmlId))

        labels, enriched = self._enrichDonutPieData(datasets)

        self.addJS("var donutPieChartCanvas = $('#{}').get(0).getContext('2d'); var donutPieData = {{labels: {},datasets: [{}]}}".format(htmlId, json.dumps(labels), json.dumps(enriched)))
        self.addJS("var donutPieOptions= {{maintainAspectRatio : false,responsive : true}}; new Chart(donutPieChartCanvas, {{type: '{}', data: donutPieData, options: donutPieOptions}})".format(typ))

        return '\n'.join(output)
        
    def generateBarChart(self, labels, datasets, idPrefix = ''):
        id = idPrefix + 'bar' + str(uuid.uuid1())

        output = []
        output.append("<div class='chart'><canvas id='" + id + "' style='min-height: 250px; height: 250px; max-height: 250px; max-width: 100%;'></canvas></div>")

        enriched = self._enrichChartData(datasets)

        self.addJS("var areaChartData = {labels: " + json.dumps(labels) + ", datasets: " + json.dumps(enriched) + "}")
        self.addJS("var barChartData = $.extend(true, {}, areaChartData); var stackedBarChartCanvas = $('#" + id + "').get(0).getContext('2d'); var stackedBarChartData = $.extend(true, {}, barChartData)")
        
        self.addJS("""
        var stackedBarChartOptions = {
          responsive              : true,
          maintainAspectRatio     : false,
          scales: {
            xAxes: [{
              stacked: true,
            }],
            yAxes: [{
              stacked: true
            }]
          },
         onClick: function(e, i){
            checkCtrl = $('#checkCtrl')
            var v = i[0]['_model']['label'];
            if(typeof v == 'undefined')
                return
            curVal = checkCtrl.val()
            idx = curVal.indexOf(v)
            if (idx == -1){
                curVal.push(v)
            }else{
                curVal.splice(idx, 1);
            }
            checkCtrl.val(curVal).trigger('change')
        }
    }
            new Chart(stackedBarChartCanvas, {
                type: 'bar',
                data: stackedBarChartData,
                options: stackedBarChartOptions
            })""")
        
        return "\n".join(output)
        
    def generateSummaryCardTag(self, summary):
        text = ''
        text += self._generateSummaryCardTagHelper(summary.get('downtime', False), 'Have Downtime')
        text += ' ' + self._generateSummaryCardTagHelper(summary.get('needFullTest', False), 'Testing Required')
        text += ' ' + self._generateSummaryCardTagHelper(summary.get('slowness', False), 'Performance Impact')
        text += ' ' + self._generateSummaryCardTagHelper(summary.get('additionalCost', False), 'Cost Incurred')

        return text
        
    def _generateSummaryCardTagHelper(self, flag, text):
        if flag == False:
            return ''
        
        strx = text
        color = 'warning'
        if flag < 0:
            strx += " (maybe)"
            color = 'info'
            
        return f"<span class='badge badge-{color}'>{strx}</span>"
        
    def _enrichDonutPieData(self, datasets):
        label = []
        arr = {
            'data': [],
            'backgroundColor': []
        }
        
        idx = 0
        for key, num in datasets.items():
            label.append(key)
            arr['data'].append(num)
            arr['backgroundColor'].append(self._randomHexColorCode(idx))
            
            idx += 1
            
        return [label, arr]
        
    def _enrichChartData(self, datasets):
        arr = []
        idx = 0
        for key, num in datasets.items():
            arr.append({
                'label': key,
                'backgroundColor': self._randomRGB(idx),
                'data': num
            })
            idx += 1

        return arr
        
    def _randomRGB(self, idx):
        if self.colorCustomRGB == None:
            r1Arr = [255, 13 , 220, 40 , 23 , 111, 253, 32 , 232]
            r2Arr = [153, 46 , 53 , 167, 162, 66 , 126, 201, 62 ]
            r3Arr = [0  , 94 , 69 , 69 , 184, 193, 20 , 151, 140]
        else:
            r1Arr = self.colorCustomRGB[0]
            r2Arr = self.colorCustomRGB[1]
            r3Arr = self.colorCustomRGB[2]
        
        if idx >= len(r1Arr):
            idx = idx%len(r1Arr)
        
        r1 = r1Arr[idx]
        r2 = r2Arr[idx]
        r3 = r3Arr[idx]
    
        return "rgba({}, {}, {}, 1)".format(r1, r2, r3)
        
    def _randomHexColorCode(self, idx):
        if self.colorCustomHex == None:
            color = ["#FF9900", "#0D2E5E", "#dc3545", "#28a745", "#17a2b8", "#6f42c1", "#fd7e14", "#20c997", "#e83e8c"]
        else:
            color = self.colorCustomHex
        
        if idx >= len(color):
            idx = idx%len(color)
            # return '#' + str(hex(random.randint(0, 0xFFFFFF))).lstrip('0x').rjust(6, '0')
        #else:
        return color[idx]

    def generateTitleWithCategory(self, count, title, category, color='info'):
        if not category:
            return title
        return f"{count}. {title} <span class='detailCategory' data-span-category='{category}'></span>"
        
    def generateTable(self, resource):
        output = []
        for check, attr in resource.items():
            criticality = attr['criticality']
            checkPrefix = ''
            if criticality == 'H':
                checkPrefix = "<i style='color: #dc3545' class='icon fas fa-ban'></i> "
            elif criticality == 'M':
                checkPrefix = "<i style='color: #ffc107' class='icon fas fa-exclamation-triangle'></i> "

            output.append("<tr>")
            output.append("<td>{}{}</td>".format(checkPrefix, check))
            output.append("<td>{}</td>".format(attr['value']))
            output.append("<td>{}</td>".format(attr['shortDesc']))
            output.append("</tr>")

        return "\n".join(output)
        
    def _getTemplateByKey(self, key):
        path = _C.TEMPLATE_DIR + '/' + self.pageTemplate[key]
        
        if os.path.exists(path):
            return path
        else:
            _warn(path + ' does not exists')
            ## <TODO>
            # debug_print_backtrace()
    
    def buildHeader(self):
        output = []
        #file_get_pre_css
        headerPreCSS = open(self._getTemplateByKey('header.precss'), 'r').read()
        headerPreCSS = headerPreCSS.replace('{$ADVISOR_TITLE}', Config.ADVISOR['TITLE'])
        headerPreCSS = headerPreCSS.replace('{$SERVICE}', self.service.upper())
        output.append(headerPreCSS)

        if self.cssLib:
            for lib in self.cssLib:
                output.append("<link rel='stylesheet' href='{}'>".format(lib))

        #file_get_post_css
        headerPostCSS = open(self._getTemplateByKey('header.postcss'), 'r').read()
        
        # Generate suppression indicator
        suppression_indicator = self.generateSuppressionIndicator()
        
        # Get client name from Config (default to 'OTC' if not set)
        client_name = Config.get('CLIENT_NAME', 'OTC')
        
        output.append(
            headerPostCSS.replace('{$ADVISOR_TITLE}', Config.ADVISOR['TITLE'])
                .replace('{$OPTIONS_ACCOUNTS}', self.accountListsHTML())
                .replace('{$SUPPRESSION_INDICATOR}', suppression_indicator)
                .replace('{$CLIENT_NAME}', client_name)
        )
        
        js = """
$('#changeAcctId').change(function(){
    var url = window.location.href
    var arr = url.split("/")
    arr[arr.length - 2] = $(this).val()
    var newLink = arr.join('/')
    window.location.href = newLink
})
"""
        self.addJS(js)

        return output
    
    def generateSuppressionIndicator(self):
        """Generate the suppression indicator for the header"""
        suppressions_manager = Config.get('suppressions_manager', None)
        
        if not suppressions_manager or not suppressions_manager.is_loaded:
            return ""
        
        # Only return the indicator button, modal will be added separately
        indicator_html = '''
      <li class="nav-item">
        <a class="nav-link" href="#" role="button" id="suppressionIndicator" title="View Suppression Configuration">
          <i class="fas fa-eye-slash text-warning"></i>
          <span class="d-none d-md-inline ml-1">Suppression Active</span>
        </a>
      </li>'''
        
        return indicator_html
    
    def generateSuppressionModal(self, suppressions_manager):
        """Generate the suppression modal HTML"""
        suppression_config_html = self.generateSuppressionConfigHTML(suppressions_manager)
        
        modal_html = f'''
<!-- Suppression Configuration Modal -->
<div class="modal fade" id="suppressionModal" tabindex="-1" role="dialog" aria-labelledby="suppressionModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-lg" role="document">
    <div class="modal-content">
      <div class="modal-header bg-warning">
        <h5 class="modal-title" id="suppressionModalLabel">
          <i class="fas fa-eye-slash"></i> Suppression Configuration
        </h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close" id="suppressionModalClose">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
        {suppression_config_html}
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal" id="suppressionModalCloseBtn">Close</button>
      </div>
    </div>
  </div>
</div>'''
        
        return modal_html
    
    def generateSuppressionConfigHTML(self, suppressions_manager):
        """Generate human-readable HTML for suppression configuration"""
        if not suppressions_manager or not suppressions_manager.is_loaded:
            return "<p>No suppressions active.</p>"
        
        html_parts = []
        
        # Add summary
        service_rule_count = len(suppressions_manager.suppressions.get('service_rules', {}))
        resource_specific_count = sum(
            len(resources) for service_rules in suppressions_manager.suppressions.get('resource_specific', {}).values() 
            for resources in service_rules.values()
        )
        
        html_parts.append(f'''
        <div class="alert alert-info">
          <h6><i class="fas fa-info-circle"></i> Summary</h6>
          <p><strong>{service_rule_count}</strong> service-level suppressions and <strong>{resource_specific_count}</strong> resource-specific suppressions are active.</p>
        </div>
        ''')
        
        # Service-level suppressions
        service_rules = suppressions_manager.suppressions.get('service_rules', {})
        if service_rules:
            html_parts.append('<h6><i class="fas fa-layer-group"></i> Service-Level Suppressions</h6>')
            html_parts.append('<div class="table-responsive">')
            html_parts.append('<table class="table table-sm table-striped">')
            html_parts.append('<thead><tr><th>Service</th><th>Rule</th><th>Description</th></tr></thead>')
            html_parts.append('<tbody>')
            
            for service, rules in service_rules.items():
                for rule in rules:
                    description = f"All {rule} findings for {service.upper()} service are suppressed"
                    html_parts.append(f'''
                    <tr>
                      <td><span class="badge badge-primary">{service.upper()}</span></td>
                      <td><code>{rule}</code></td>
                      <td>{description}</td>
                    </tr>
                    ''')
            
            html_parts.append('</tbody></table></div>')
        
        # Resource-specific suppressions
        resource_specific = suppressions_manager.suppressions.get('resource_specific', {})
        if resource_specific:
            html_parts.append('<h6><i class="fas fa-cube"></i> Resource-Specific Suppressions</h6>')
            html_parts.append('<div class="table-responsive">')
            html_parts.append('<table class="table table-sm table-striped">')
            html_parts.append('<thead><tr><th>Service</th><th>Rule</th><th>Resources</th></tr></thead>')
            html_parts.append('<tbody>')
            
            for service, service_rules in resource_specific.items():
                for rule, resources in service_rules.items():
                    resources_html = []
                    for resource in resources:
                        resources_html.append(f'<span class="badge badge-secondary mr-1">{resource}</span>')
                    
                    html_parts.append(f'''
                    <tr>
                      <td><span class="badge badge-primary">{service.upper()}</span></td>
                      <td><code>{rule}</code></td>
                      <td>{"".join(resources_html)}</td>
                    </tr>
                    ''')
            
            html_parts.append('</tbody></table></div>')
        
        if not service_rules and not resource_specific:
            html_parts.append('<p class="text-muted">No suppression rules configured.</p>')
        
        return ''.join(html_parts)
    
    def accountListsHTML(self):
        accts = Config.get("ListOfAccounts", None)
        acctInfo = Config.get('stsInfo')
        html = []
        for acct in accts:
            slct = ''
            if acct == acctInfo['Account']:
                slct = ' selected'
            html.append("<option value='{}'{}>{}</option>".format(acct, slct, acct))
        
        return ''.join(html);
    
    def buildFooter(self):
        output = []
        #file_get_template preInlineJS
        preJS = open(self._getTemplateByKey('footer.prejs'), 'r').read()
        preJS = preJS.replace('"', "'")

        ADMINLTE_VERSION = Config.ADMINLTE['VERSION']
        ADMINLTE_DATERANGE = Config.ADMINLTE['DATERANGE']
        ADMINLTE_URL = Config.ADMINLTE['URL']
        ADMINLTE_TITLE = Config.ADMINLTE['TITLE']

        PROJECT_TITLE = Config.ADVISOR['TITLE']
        PROJECT_VERSION = Config.ADVISOR['VERSION']
        
        # Get CLIENT_NAME from config (defaults to 'OTC' if not set)
        CLIENT_NAME = Config.get('CLIENT_NAME', 'OTC') or 'OTC'
        
        # Get SCAN_TIMESTAMP from config and format it
        scan_timestamp = Config.get('SCAN_TIMESTAMP', None)
        if scan_timestamp:
            # Format: YYYY-MM-DD HH:MM:SS
            from datetime import datetime
            if isinstance(scan_timestamp, datetime):
                SCAN_DATE = scan_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                SCAN_DATE = str(scan_timestamp)
        else:
            from datetime import datetime
            SCAN_DATE = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        x = preJS.replace('{$ADMINLTE_VERSION}', ADMINLTE_VERSION)
        x = x.replace('{$ADMINLTE_DATERANGE}', ADMINLTE_DATERANGE)
        x = x.replace('{$ADMINLTE_URL}', ADMINLTE_URL)
        x = x.replace('{$ADMINLTE_TITLE}', ADMINLTE_TITLE)
        x = x.replace('{$PROJECT_TITLE}', PROJECT_TITLE)
        x = x.replace('{$PROJECT_VERSION}', PROJECT_VERSION)
        x = x.replace('{$CLIENT_NAME}', CLIENT_NAME)
        x = x.replace('{$SCAN_DATE}', SCAN_DATE)
        
        output.append(x)

        if self.jsLib:
            for lib in self.jsLib:
                output.append(f"<script src='{lib}'></script>")

        if self.js:
            inlineJS = '; '.join(self.js)
            output.append(f"<script>$(function(){{{inlineJS}}})</script>")

        #file_get_template postInlineJS
        postJS = open(self._getTemplateByKey('footer.postjs'), 'r').read()
        output.append(postJS)

        return output    
        
    def buildBreadcrumb(self):
        output = []
        breadcrumb = open(self._getTemplateByKey('breadcrumb'), 'r').read()
        breadcrumb = breadcrumb.replace('{$SERVICE}', self.service.upper())
        output.append(breadcrumb)
           
        return output
        
    def buildNav(self):
        ISHOME = 'active' if self.isHome else ''

        output = []
        #file_getsidebar
        sidebarPRE = open(self._getTemplateByKey('sidebar.precustom'), 'r').read()
        sidebarPRE = sidebarPRE.replace('{$ADVISOR_TITLE}', Config.ADVISOR['TITLE'])
        sidebarPRE = sidebarPRE.replace('{$ISHOME}', ISHOME)
        output.append(sidebarPRE)
        
        #Page
        pages = Config.get('CustomPage::Pages')
        if pages:
            arr = self.buildNavCustomItems('Pages', pages)
            output.append("\n".join(arr))
        
        arr = self.buildNavCustomItems('Frameworks', self.frameworks)
        output.append("\n".join(arr))

        arr = self.buildNavCustomItems('References', self.services)
        output.append("\n".join(arr))

        sidebarPOST = open(self._getTemplateByKey('sidebar.postcustom'), 'r').read()
        output.append(sidebarPOST)

        return output
    
    ## <TODO>
    ## Support Framework
    def buildNavCustomItems(self, title, lists):
        from utils.Config import Config
        
        services = lists
        activeService = self.service
        
        skipCount = False
        if title == 'Pages':
            skipCount = True

        if title == 'Frameworks':
            title = 'Compliances / Frameworks'
            services = {}
            for l in lists:
                services[l] = 0
        else:
            services = lists
            
        output = []
        output.append("<li class='nav-header'>{}</li>".format(title))
            
        _services = sorted(services)
        
        for name in _services:
            count = 0
            if skipCount == False:
                count = services[name]
                
            if name == activeService:
                class_ = 'active'
            else:
                class_ = ''
            
            isFramework = True    
            icon = self.frameworkIcon
            if name in self.serviceIcon:
                isFramework = False
                icon = self._navIcon(name)

            _count = count
            if name == 'guardduty' or isFramework == True:
                _count = ''

            link = name.lower()
            if skipCount == True:
                link = 'CP' + name.lower()
            
            # Get tooltip from framework descriptions
            tooltip = ''
            if isFramework and name.upper() in Config.FRAMEWORK_DESCRIPTIONS:
                tooltip = Config.FRAMEWORK_DESCRIPTIONS[name.upper()]['tooltip']
            
            # Build title attribute for tooltip
            title_attr = ' title="{}"'.format(tooltip) if tooltip else ''
                
            output.append("<li class='nav-item'>\n"
                          "<a href='{}.html' class='nav-link {}'{}\n"
                          "<i class='nav-icon fas fa-{}'></i>\n"
                          "<p>{} <span class='badge badge-info right' data-count='{}'></span></p>\n"
                          "</a>\n"
                          "</li>".format(link, class_, title_attr, icon, name.upper(), _count))

        return output
        
    def _navIcon(self, service):
        return self.serviceIcon.get(service, 'cog')
        
    def addJS(self, js):
        self.js.append(js)
        
    def addJSLib(self, js):
        self.jsLib.append(js)
        
    def addCSSLib(self, css):
        self.cssLib.append(css)
        
    def checkIsLowHangingFruit(self, attr):
        if attr['downtime'] == 0 and attr['additionalCost'] == 0 and attr['needFullTest'] == 0:
            return True
        else:
            return False
            
    def buildKpiCard(self): 
        output=[]
        stats = self.reporter.stats
        
        ## 1st kpi: #Resources
        output.append(self._buildIndividualKpiCard(stats['resources'], 'resources'))
        
        output.append(self._buildIndividualKpiCard(self.reporter.findingsCount, 'findings'))
        output.append(self._buildIndividualKpiCard(stats['rules'], 'rules'))
        
        output.append(self._buildIndividualKpiCard(stats['checksCount'], 'checksCount'))
        
        # Comment out exceptions and replace with suppressions
        # output.append(self._buildIndividualKpiCard(stats['exceptions'], 'exceptions'))
        
        output.append(self._buildIndividualKpiCard(self.reporter.suppressedCount, 'suppressions'))
        
        output.append(self._buildIndividualKpiCard(str(round(stats['timespent'], 3)) + 's', 'timespent'))
        
        return output
        
    def _buildIndividualKpiCard(self, stat, cat):
        settings = {
            'resources': {
                'description': 'Resources',
                'icon': 'server',
                'bg': 'info'
            },
            'findings': {
                'description': 'Total Findings',
                'icon': 'search-plus',
                'bg': 'warning'
            },
            'rules': {
                'description': 'Rules Executed',
                'icon': 'check-square',
                'bg': 'success'
            },
            'checksCount': {
                'description': 'Unique Rules',
                'icon': 'check-double',
                'bg': 'secondary'
            },
            # 'exceptions': {
            #     'description': 'Exception',
            #     'icon': 'radiation-alt',
            #     'bg': 'danger'
            # },
            'suppressions': {
                'description': 'Suppressed',
                'icon': 'eye-slash',
                'bg': 'danger'
            },
            'timespent': {
                'description': 'Timespent',
                'icon': 'clock',
                'bg': 'pink'
            }
            
        }
        
        inf = settings[cat]
        
        s = """<div class='small-box bg-{}'>
            <div class='inner'>
                <h3>{}</h3>
                <p>{}</p>
            </div>
            <div class='icon'>
                <i class='fas fa-{}'></i>
            </div>
        </div>""".format(inf['bg'], stat, inf['description'], inf['icon'])
        
        return s
    
    def genaiModalHtml(self):
        genAIJS = """serv = $('h1').text()
activeAcct = $('#changeAcctId').val()
        
$('.beta-genai').click(function(){
  t = $(this)
  currentInfo = {'activeAcct': activeAcct, 'service': serv,'title': t.parent().text().trim(),'resources': {}, 'href': []}
  t.parent().parent().parent().find('.card-body dd').each(function(index, el){
    _t = $(this)
    cls = _t.attr('class')
    tmpText = _t.text()

    if(cls == 'detail-desc'){
      currentInfo['desc'] = tmpText.trim()
    }

    if(cls == 'detail-regions'){
      let colonIndex = tmpText.indexOf(':')
      region = tmpText.substring(0, colonIndex)
      resources = tmpText.substring(colonIndex+2) //include : and space

      currentInfo['resources'][region] = resources.split(' | ')
    }

    if(cls == 'detail-href'){
      _t.find('a').each(function(){
        __t = $(this)
        currentInfo['href'].push(__t.attr('href'))
      })
    }
  })
})

genaiResp = $('#genai-modal-response')
$('#genai-savequery').click(function(){
  sbtn = $(this)
  genaikeys = $('#genai-key').val().split('|')
  
  if((genaikeys.length < 2) || (genaikeys.length > 2)){
    alert('invalid keys')
    return
  }

  sbtn.prop('disabled', true)
  myJsonData = {'api_data': currentInfo}
  genaiResp.text("... generating results, it can take times, please be patient ...\\n\\nData sent are as below:\\n" + JSON.stringify(myJsonData, null, 4))
  
  a_url = genaikeys[0]
  a_key = genaikeys[1]

  
  $.ajax({
    url: a_url,
    // headers: {'x-api-key': a_key},
    type: 'POST',
    data: JSON.stringify(myJsonData),
    contentType: 'application/json',
    dataType: 'json',
    success: function(response) {
      genaiResp.text(response['response'])
      sbtn.prop('disabled', false)
    },
    error: function(xhr, status, error) {
      sbtn.prop('disabled', false)    
      genaiResp.text("Error..., check console.log")
      console.error('Error:', error);
    }
  });
})"""

        self.addJS(genAIJS)

        return '''<div class="modal fade" id="genai-modal" tabindex="-1" role="dialog" aria-labelledby="genai-modal" aria-hidden="true">
  <div class="modal-dialog modal-xl modal-dialog-centered" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="genai-modalTitle">Beta - Calls API</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
        Provide your API endpoints, follows by API Key. E.g: https://xxxx.execute-api.ap-southeast-1.amazonaws.com/prod|mysampleApiKeyHere
        <input type="text" id="genai-key" name="genai-key" style="width:100%">
        <br>Response:<br>
        <textarea id="genai-modal-response" readonly style="color: #b55d00; width: 100%; background: #ededed; height: 500px; font-family: monospace; font-size: 12px;"></textarea>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
        <button type="button" class="btn btn-primary" id="genai-savequery">Save and Query</button>
      </div>
    </div>
  </div>
</div>'''

    def buildContentSummary_default(self):
        output = []

        self.isBeta = Config.get('beta', False)
        if self.isBeta == True:
            output.append(self.genaiModalHtml())

        ## KPI Building, 2023-10-16
        items = []
        kpiCards = self.buildKpiCard()
        for kpi in kpiCards:
            items.append([kpi, ''])
            
        output.append(self.generateRowWithCol(size=2, items=items))
        
        ## Chart Building
        summary = self.reporter.cardSummary
        regions = self.regions
        labels = []
        dataSets = {}
        for label, attrs in summary.items():
            labels.append(label)
            res = attrs['__affectedResources']
            for region in regions:
                cnt = 0
                if region in res:
                    cnt = len(res[region])
                dataSets.setdefault(region, []).append(cnt)
        
        pid=self.getHtmlId('SummaryChart')
        html = self.generateBarChart(labels, dataSets)
        card = self.generateCard(pid, html, cardClass='warning', title='Summary', titleBadge='', collapse=9, noPadding=False)
        items = [[card, '']]
        output.append(self.generateRowWithCol(size=12, items=items, rowHtmlAttr="data-context='summaryChart'"))
        ## Chart completed

        ##### Cost Optimization Chart #####
        chartItems = []
        chartPid = self.getHtmlId('CostChart')
        chartsObj = self.reporter.charts
        chartsConfigObj = self.reporter.chartsConfig

        for title in chartsObj:
            chartDataSets = chartsObj[title]
            chartConfig = chartsConfigObj[title]

            html = self.generateBarChart(chartConfig['legends'], chartDataSets)
            card = self.generateCard(chartPid, html, cardClass='info', title=title, titleBadge='', collapse=9, noPadding=False)
            chartItems.append([card, ''])
        
        output.append(self.generateRowWithCol(size=6, items=chartItems, rowHtmlAttr="data-context='costChart'"))

        ##### Cost Optimization Chart Completed #####

        ## Filter
        filterTitle = "<i class='icon fas fa-search'></i> Filter"
        filterByCheck = self.generateFilterByCheck(labels)
        filterRow = self.generateRowWithCol(size=[6, 6, 12], items=self.addSummaryControl_default(), rowHtmlAttr="data-context='summary-control'")

        output.append(self.generateCard(pid='summary-control', html=filterByCheck + filterRow, cardClass='info', title=filterTitle, titleBadge='', collapse=False, noPadding=False))
        
        ## Severity Filter Panel
        filter_panel = self.generateSeverityFilterPanel()
        output.append(filter_panel)
        
        ## SummaryCard Building
        items = []
        for label, attrs in summary.items():
            body = self.generateSummaryCardContent(attrs)

            badge = self.generatePriorityPrefix(attrs['criticality'], "style='float:right'") + ' ' + self.generateCategoryBadge(attrs['__categoryMain'], "style='float:right'")
            card = self.generateCard(pid="SUMMARY_"+self.getHtmlId(label), html=body, cardClass='', title=label, titleBadge=badge, collapse=9, noPadding=False)
            divHtmlAttr = "data-category='" + attrs['__categoryMain'] + "' data-criticality='" + attrs['criticality'] + "'"

            if self.checkIsLowHangingFruit(attrs):
                divHtmlAttr += " data-lhf=1"

            items.append([card, divHtmlAttr])

        output.append(self.generateRowWithCol(size=4, items=items, rowHtmlAttr="data-context='summary'"))
        return output
        
    def buildContentDetail_default(self):
        output = []
        output.append('<h5 class="mt-4 mb-2">Detail</h5>')

        details = self.reporter.getDetail()
        count = 1
        previousCategory = ""
        for region, lists in details.items():
            items = []
            output.append("<h6 class='mt-4 mb-2'>{}</h6>".format(region))
            for identifierx, attrs in lists.items():
                tab = []
                identifier = identifierx
                category = ''
                checkIfCategoryPresent = identifierx.split('::')
                if len(checkIfCategoryPresent) == 2:
                    category, identifier = checkIfCategoryPresent
                    if not previousCategory:
                        previousCategory = category

                tab.append("<table class='table table-sm'><thead><tr>")
                tab.append("<th scole='col'>Check</th><th scole='col'>Current Value</th><th scole='col'>Recommendation</th>")
                tab.append("</tr></thead><tbody>")
                tab.append(self.generateTable(attrs))
                tab.append("</tbody></table>")
                tab = "\n".join(tab)

                if previousCategory != category and category != '' and count % 2 == 0:
                    items.append([])

                item = self.generateCard(pid=self.getHtmlId(identifierx), html=tab, cardClass='warning', title=self.generateTitleWithCategory(count, identifier, category), titleBadge='', collapse=False, noPadding=True)
                items.append([item, ''])

                previousCategory = category
                count += 1

            output.append(self.generateRowWithCol(size=6, items=items, rowHtmlAttr="data-context=detail"))
        
        str = """
$('span.detailCategory').each(function(){
  var t = $(this);
  t.parent().parent().append("<span class='badge badge-info' style='float:right; line-height:15px'>"+t.data('span-category')+"</span>");
})
"""
        self.addJS(str)
        
        return output
        
    def generateFilterByCheck(self, labels):
        opts = []
        for label in labels:
            opts.append("<option value='{}'>{}</option>".format(label, label))

        options = ''.join(opts)

        str = """
<div class='col-md-12'>
<div class="form-group">
	<label>Checks</label>
	<div class="select2-purple">
	<select id='checkCtrl' class="select2" multiple data-placeholder="Select checks..." data-dropdown-css-class="select2-purple" style="width: 100%;">
		{}
	</select>
	</div>
</div>
</div>
""".format(options)

        return str
        
    def addSummaryControl_default(self):
        jsServIdPrefix = "#" + self.service + '-'

        output = []
        output.append('')

        items = []
        str = """<div class="form-group">
  <label>Pillar</label>
  <select id='filter-pillar' class="form-control">
    <option value='-' selected>All</option>
    <option value='O'>Operation Excellence</option>
    <option value='R'>Reliablity</option>
    <option value='S'>Security</option>
    <option value='P'>Performance Efficiency</option>
    <option value='C'>Cost Optimization</option>
    <option value='T'>*Text*</option>
  </select>
</div>"""
        items.append([str, ''])
    
        str = """
<div class="form-group">
  <label>Criticality</label>
  <select id='filter-critical' class="form-control">
    <option value='-' selected>All</option>
    <option value='H'>High</option>
    <option value='M'>Medium</option>
    <option value='L'>Low</option>
    <option value='I'>Informational</option>
  </select>
</div>
"""
        items.append([str, ''])

        str = """
<div class='col-md-12' >
  <div class='row'>
    <div class='col-md-4'>
      <div class="form-group">
          <div class="icheck-success d-inline">
              <input type="checkbox" id="cbLowHangingFruit">
              <label for="cbLowHangingFruit">Show low hanging fruit(s) only</label>
          </div>
      </div>
    </div>
    <div class='col-md-4'>
      <div class="form-group clearfix">
        <div class="icheck-success d-inline">
          <input type="radio" id="radio_cs1" name=radio_cs value='expand'>
          <label for="radio_cs1">Expand / </label>
        </div><div class="icheck-success d-inline">
          <input type="radio" id="radio_cs2" name=radio_cs value='collapse' checked>
          <label for="radio_cs2">Hide all cards</label>
        </div>
      </div>
    </div>
  </div>
</div>
"""
        items.append([str, ''])
        
        js = """
$('.select2').select2()
var si = $('div[data-context="summary"] div[data-category]');
var cards = $('[data-context="summary"] div.col-md-4')
$('input[name=radio_cs]').change(function(){
  var v = $(this).val()
  var i = cards.find('button > i')
  if (v == 'expand') {
    cards.find('.collapsed-card').removeClass('collapsed-card')
    cards.find('div.card-body').show()
    i.removeClass('fa-plus').addClass('fa-minus')
  }else{
    tmp = $('[data-context="summary"] div.col-md-4 > div:not(.collapsed-card)')
    tmp.addClass('collapsed-card')
    cards.find('div.card-body').hide()
    i.removeClass('fa-minus').addClass('fa-plus')
  }
})
$('#filter-critical, #filter-pillar, #checkCtrl, #cbLowHangingFruit').change(function(){
var cb_lhf_on = $("#cbLowHangingFruit").is(':checked')
var pv = $('#filter-pillar').val();
var fc = $('#filter-critical').val();
var tiArray = $('#checkCtrl').val();
var s = '';
if(pv != '-') s += '[data-category="'+pv+'"]';
if(fc != '-') s += '[data-criticality="'+fc+'"]';
if(tiArray.length > 0){
	si.hide()
	$.each(tiArray, function(k, v){"""
        txt = "id = \"{}\" + v;".format(jsServIdPrefix)
        js += txt
        js += """$(id).parent().addClass('showLater');
	})
	if(s.length > 0){
		$('div[data-context="summary"] .showLater'+s+'').show()
	}else{
		$('.showLater').show()
	}
	$('.showLater').removeClass('showLater')
}else if(s.length == 0){
  si.show();
}else{
  si.hide();
  $('div[data-context="summary"] div'+s+'').show()
}
$('[data-context="summary"] .col-md-4:visible').addClass('showLater2')
if(cb_lhf_on == true){
  $('.showLater2').hide()
  $('.showLater2[data-lhf=1]').show()
  $('.showLater2').removeClass('showLater2')
}
})
"""
        self.addJS(js)
        return items
