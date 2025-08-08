#!/bin/bash

# Demo script to showcase the modular claude_work system

echo "=== Claude Work Modular System Demo ==="
echo ""

echo "1. Running Phase 1 (Session Initialization):"
echo "   ./claude_work.sh phase 1 'Demo task setup'"
echo ""

echo "2. Running Phase 2 (Task Selection & Analysis):"
echo "   ./claude_work.sh phase 2 'Analyze available tasks and select one to work on'"
echo ""

echo "3. Running Phase 3 (Implementation Planning):"
echo "   ./claude_work.sh phase 3 'Create detailed implementation plan for selected task'"
echo ""

echo "4. Running Phase 4 (Code Implementation):"
echo "   ./claude_work.sh phase 4 'Execute the implementation plan and modify code'"
echo ""

echo "5. Running Phase 5 (Testing & Documentation):"
echo "   ./claude_work.sh phase 5 'Test implementation and create completion documentation'"
echo ""

echo "=== Available Instruction Files ==="
echo "Core instructions (always included):"
ls -la implementation_results/claude_work_core.md 2>/dev/null || echo "  ❌ claude_work_core.md not found"

echo ""
echo "Phase-specific instructions:"
for i in {1..5}; do
    if [ -f "implementation_results/claude_work_phase${i}.md" ]; then
        size=$(wc -l < "implementation_results/claude_work_phase${i}.md")
        echo "  ✅ Phase $i: claude_work_phase${i}.md ($size lines)"
    else
        echo "  ❌ Phase $i: claude_work_phase${i}.md not found"
    fi
done

echo ""
echo "Reference files:"
ls -la implementation_results/claude_work_templates.md 2>/dev/null && echo "  ✅ Templates available" || echo "  ❌ Templates not found"
ls -la implementation_results/claude_work_troubleshooting.md 2>/dev/null && echo "  ✅ Troubleshooting guide available" || echo "  ❌ Troubleshooting guide not found"

echo ""
echo "=== Benefits of Modular System ==="
echo "✅ Claude gets focused, phase-specific instructions (30-50 lines vs 572 lines)"
echo "✅ Reduced cognitive load and improved instruction following"
echo "✅ Just-in-time information delivery"
echo "✅ Easier maintenance and updates of individual phases"
echo "✅ Better structured workflow"
echo "✅ Reference materials available on-demand"

echo ""
echo "=== Instruction File Sizes ==="
echo "Old monolithic file:"
ls -la implementation_results/claude_work_instructions.md 2>/dev/null | awk '{print "  " $9 ": " $5 " bytes"}' || echo "  claude_work_instructions.md not found"

echo ""
echo "New modular files:"
total_size=0
for file in implementation_results/claude_work_core.md implementation_results/claude_work_phase*.md implementation_results/claude_work_templates.md implementation_results/claude_work_troubleshooting.md; do
    if [ -f "$file" ]; then
        size=$(wc -c < "$file" 2>/dev/null || echo 0)
        lines=$(wc -l < "$file" 2>/dev/null || echo 0)
        echo "  $(basename "$file"): $size bytes ($lines lines)"
        total_size=$((total_size + size))
    fi
done
echo "  Total modular size: $total_size bytes"

echo ""
echo "Demo complete! The modular system is ready for use."
