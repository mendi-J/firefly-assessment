#!/bin/bash

# Pre-Push Validation Script
# Run this before pushing to GitHub to ensure CI will pass

set -e

echo "🔍 Running pre-push validation checks..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# 1. Check if Python is available
echo "1️⃣  Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ ${PYTHON_VERSION}${NC}"
else
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi
echo ""

# 2. Install dependencies
echo "2️⃣  Installing dependencies..."
python3 -m pip install -q -r requirements.txt
python3 -m pip install -q black flake8 pytest-cov
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# 3. Format code with Black
echo "3️⃣  Formatting code with Black..."
if python3 -m black .; then
    echo -e "${GREEN}✅ Code formatted${NC}"
else
    echo -e "${RED}❌ Black formatting failed${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 4. Run Flake8 (critical errors only)
echo "4️⃣  Running Flake8 linter (critical errors)..."
if python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=venv,env,.git,__pycache__,.pytest_cache; then
    echo -e "${GREEN}✅ No critical lint errors${NC}"
else
    echo -e "${RED}❌ Flake8 found critical errors${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 5. Run all tests
echo "5️⃣  Running test suite..."
if python3 -m pytest tests/ -v --tb=short; then
    echo -e "${GREEN}✅ All tests passed${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 6. Test with coverage
echo "6️⃣  Checking test coverage..."
if python3 -m pytest tests/ --cov=. --cov-report=term-missing --cov-fail-under=80; then
    echo -e "${GREEN}✅ Coverage check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Coverage below 80% (warning only)${NC}"
fi
echo ""

# 7. Run functional test
echo "7️⃣  Running functional test..."
if python3 main.py --cloud examples/cloud_resources.json --iac examples/iac_resources.json --output /tmp/validation-report.json > /dev/null 2>&1; then
    if python3 -c "import json; data=json.load(open('/tmp/validation-report.json')); assert len(data) == 4; assert all(k in data[0] for k in ['CloudResourceItem', 'IacResourceItem', 'State', 'ChangeLog'])"; then
        echo -e "${GREEN}✅ Functional test passed${NC}"
        rm -f /tmp/validation-report.json
    else
        echo -e "${RED}❌ Report validation failed${NC}"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo -e "${RED}❌ Functional test failed${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# 8. Verify required files exist
echo "8️⃣  Checking required files..."
REQUIRED_FILES=(
    "main.py"
    "analyzer.py"
    "models.py"
    "utils.py"
    "requirements.txt"
    "README.md"
    "examples/cloud_resources.json"
    "examples/iac_resources.json"
    "tests/test_analyzer.py"
    ".github/workflows/ci.yml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file ${RED}(missing)${NC}"
        FAILURES=$((FAILURES + 1))
    fi
done
echo ""

# Final summary
echo "═══════════════════════════════════════════"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}🎉 All validation checks passed!${NC}"
    echo -e "${GREEN}✅ Ready to push to GitHub${NC}"
    echo ""
    echo "Next steps:"
    echo "  git add ."
    echo "  git commit -m 'Your commit message'"
    echo "  git push origin main"
    exit 0
else
    echo -e "${RED}❌ ${FAILURES} check(s) failed${NC}"
    echo -e "${RED}⚠️  Please fix the issues before pushing${NC}"
    exit 1
fi
