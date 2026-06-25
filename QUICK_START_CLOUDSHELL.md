# AWS Environment Assessment Tool - Quick Start Guide

## Overview

This guide provides step-by-step instructions to deploy and test the AWS Environment Assessment Tool in AWS CloudShell. The tool performs a comprehensive analysis of your AWS infrastructure against Well-Architected Framework best practices, generating an executive-ready assessment report with findings and remediation recommendations.

**Time Required:** Approximately 30 minutes
**AWS Service:** CloudShell (included in AWS Free Tier)
**Prerequisites:** Valid AWS Account with appropriate IAM permissions

---

## Prerequisites

Before beginning, ensure you have:

1. **AWS Account Access** - with appropriate read-only permissions
2. **IAM Permissions** - the following are required:
   - `ec2:Describe*` (for infrastructure assessment)
   - `iam:Get*` and `iam:List*` (for security configuration review)
   - `s3:GetBucketPolicy`, `s3:ListBucket` (for storage assessment)
   - Complete policy: `ReadOnlyAccess` (AWS managed policy)

3. **Resources in at least one AWS region** - the tool can scan empty environments, but results are more meaningful with deployed workloads

---

## Installation and Setup

### Step 1: Initialize Environment (5 minutes)

Copy and paste the following commands into AWS CloudShell:

```bash
# Create isolated Python environment
cd /tmp
python3 -m venv assessment-env
source assessment-env/bin/activate
python3 -m pip install --upgrade pip

# Clone and prepare the assessment tool
rm -rf service-screener-v2
git clone https://github.com/otc-olmo-tech-consulting/service-screener-v2
cd service-screener-v2

# Install dependencies
pip install -r requirements.txt
python3 unzip_botocore_lambda_runtime.py

# Create convenient command alias
alias screener='python3 $(pwd)/main.py'
```

**Expected Output:**
```
Cloning into 'service-screener-v2'...
Successfully installed boto3-1.35.x, packaging-23.1.x, ...
(No errors should appear)
```

---

## Running Your First Assessment

### Step 2: Verify Installation (2 minutes)

Run a quick validation to ensure everything is configured correctly:

```bash
# Verify AWS credentials are available
aws sts get-caller-identity

# Expected output (your AWS account information):
# {
#     "UserId": "AIDAI...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-username"
# }
```

If you see an error, your AWS credentials are not properly configured in CloudShell.

---

### Step 3: Run Initial Assessment (10-15 minutes)

Execute a scan of your AWS infrastructure:

```bash
# Scan a single region with core services
screener --regions us-east-1 --services ec2,iam,s3,rds,lambda

# Alternative: Scan all regions (longer running)
screener --regions ALL

# For faster results with limited scope:
screener --regions us-east-1 --services iam
```

**Expected Output:**
```
[STATUS] Scanning EC2 in us-east-1...
[STATUS] Scanning IAM...
[STATUS] Scanning S3...
[STATUS] Assessment complete
[DONE] Output generated: output.zip
```

The assessment typically takes 5-15 minutes depending on the number of resources and regions scanned.

---

### Step 4: Review Results (5 minutes)

Once the scan completes, verify the output was generated:

```bash
# Confirm output file exists
ls -lh output.zip

# Extract the assessment report
unzip -q output.zip

# Verify report files were created
find adminlte/aws -name "*.html" -type f | head -5
```

**Expected Output:**
```
-rw-r--r-- 1 user user 2.5M output.zip
index.html
ec2.html
iam.html
s3.html
```

---

### Step 5: Download Assessment Report

Your assessment report is ready for download:

#### Option A: Download via AWS CloudShell UI (Recommended)
1. In the CloudShell window, click the **Actions** button (top-right)
2. Select **Download file**
3. Enter the file path: `output/adminlte/aws/index.html`
4. Open the downloaded HTML file in your web browser

#### Option B: Download via Command Line
```bash
# If you have AWS CLI configured for S3 access (optional):
aws s3 cp output.zip s3://your-bucket-name/assessments/
```

---

## Understanding Your Assessment Report

### Report Contents

Your assessment report includes:

**Executive Dashboard:**
- Overall infrastructure health score (0-100)
- Risk distribution by severity (High, Medium, Low)
- Top 5 critical findings requiring attention
- Well-Architected Framework pillar assessment

**Service Assessments:**
- Individual findings for each AWS service (EC2, IAM, S3, RDS, Lambda, etc.)
- Security configuration issues
- Reliability and availability concerns
- Cost optimization opportunities
- Operational excellence recommendations

**Remediation Guidance:**
- Specific steps to address each finding
- AWS service documentation links
- Best practice recommendations
- Priority-based action items

---

## Advanced Options

### Custom Client Branding

Personalize the report with your organization name:

```bash
screener --regions us-east-1 --client "Acme Corporation"
```

Output file will be named: `Acme-Corporation_20250115_findings.zip`

### Using a Suppression File

Exclude known and accepted findings from the report:

```bash
# Create suppressions.json
cat > suppressions.json << 'EOF'
{
  "metadata": {
    "version": "1.0",
    "description": "Approved exceptions for Acme Corp"
  },
  "suppressions": [
    {
      "service": "s3",
      "rule": "BucketVersioning"
    },
    {
      "service": "ec2",
      "rule": "SecurityGroupOpenToAll"
    }
  ]
}
EOF

# Run assessment with suppressions
screener --regions us-east-1 --suppress_file ./suppressions.json
```

### Tag-Based Resource Filtering

Assess only resources matching specific tags:

```bash
# Scan only production resources
screener --regions us-east-1 --tags env=production

# Multiple tag filters
screener --regions us-east-1 --tags env=prod,department=infrastructure
```

---

## Troubleshooting

### Issue: "Access Denied" Error

**Problem:** Assessment fails with permission denied messages

**Solution:**
1. Verify your IAM user has `ReadOnlyAccess` policy attached
2. Check session credentials:
   ```bash
   aws sts get-caller-identity
   ```
3. If credentials are missing, restart CloudShell

### Issue: Assessment Takes Too Long

**Problem:** Scan appears to be hanging or running indefinitely

**Solution:**
1. Press `Ctrl+C` to stop the current scan
2. Run with fewer regions/services:
   ```bash
   screener --regions us-east-1 --services iam
   ```
3. Check for network issues

### Issue: Empty or Missing Report Data

**Problem:** Assessment completes but report shows no findings

**Solution:**
1. Verify resources exist in the scanned regions:
   ```bash
   aws ec2 describe-instances --region us-east-1
   aws iam list-users
   ```
2. If resources exist, run with debug output:
   ```bash
   screener --regions us-east-1 --debug
   ```

### Issue: Report File Won't Download

**Problem:** CloudShell download button is unavailable

**Solution:**
1. From CloudShell menu, select **Upload/Download**
2. Manually navigate to the output file location
3. Alternatively, provide file path directly to the download dialog

---

## Quick Reference

### Common Assessment Scenarios

#### Baseline Security Assessment (Fastest)
```bash
screener --regions us-east-1 --services iam,ec2
```
Duration: ~3-5 minutes | Focus: Security posture

#### Complete Infrastructure Audit
```bash
screener --regions ALL
```
Duration: ~30-45 minutes | Focus: Comprehensive review across all services and regions

#### Compliance Assessment
```bash
screener --regions us-east-1,eu-west-1 --services ec2,iam,s3,rds
```
Duration: ~10-15 minutes | Focus: Core compliance domains

#### Cost Optimization Review
```bash
screener --regions ALL --services ec2,rds,lambda,s3
```
Duration: ~20-30 minutes | Focus: Cost efficiency opportunities

### Essential Commands

```bash
# View all available options
screener --help

# List supported AWS services
screener --list-services

# Activate the assessment environment
source /tmp/assessment-env/bin/activate

# Deactivate environment
deactivate

# Check current assessment progress
ps aux | grep screener

# Clean up from previous assessments
rm -rf output output.zip adminlte/aws/*
```

---

## Success Criteria

Your assessment is complete and successful when:

- Assessment tool completes without errors
- Output file (`output.zip`) is generated
- HTML report file (`index.html`) is accessible
- Report displays:
  - Infrastructure health score
  - Service assessments
  - Finding descriptions with remediation steps
  - Well-Architected Framework evaluation

---

## Next Steps After Assessment

### 1. Review Executive Dashboard
- Examine overall health score and risk distribution
- Identify top 5 critical findings
- Note priority action items

### 2. Prioritize Remediation
- Review findings by severity (High → Medium → Low)
- Identify quick wins (easy to implement improvements)
- Plan resource allocation for remediation efforts

### 3. Create Action Plan
- Assign findings to responsible teams
- Establish timeline for remediation
- Define success metrics for each action item

### 4. Track Progress
- Schedule regular follow-up assessments
- Monitor remediation progress
- Re-run assessment to validate improvements

---

## Support and Documentation

For detailed information about specific findings or remediation steps:

1. Click the "Learn More" link in any finding
2. Review AWS Well-Architected Framework documentation
3. Consult AWS service-specific best practices guides

---

## Assessment Data Privacy

The assessment tool:

- **Never modifies** any AWS resources (read-only access)
- **Does not collect or transmit** sensitive data externally
- **Generates reports** that should be stored securely
- **Requires local hosting** of HTML reports (not internet-accessible)

All data remains within your AWS account. No metrics or findings are shared with external services.

---

## Frequently Asked Questions

**Q: How often should I run assessments?**
A: Recommended quarterly for regular environments, or after significant infrastructure changes.

**Q: Can I run this on a production environment?**
A: Yes. The tool is read-only and performs no modifications. It is safe for production environments.

**Q: What AWS regions are supported?**
A: All standard AWS regions. Specialized regions (China, GovCloud) may have limitations.

**Q: How is the health score calculated?**
A: The score uses a weighted algorithm: High-severity findings (3x weight) + Medium findings (1.5x weight) + Low findings (0.5x weight).

**Q: Can I customize the report?**
A: Yes. You can add your organization name using the `--client` parameter and suppress known exceptions with a suppressions file.

**Q: Is this tool approved for compliance audits?**
A: It provides supporting documentation for compliance reviews. Always consult with your compliance or audit team for formal requirements.

---

**Questions or issues?** Review the troubleshooting section above or contact your IT support team.

---

*Last Updated: January 2025*  
*Tool Version: 2.5.0*  
*Status: Production Ready*
