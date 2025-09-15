# Release Summary v10.0.8

**Release Date**: August 18, 2025  
**Release Type**: Bug Fix Release  
**PyPI**: https://pypi.org/project/emailer-simple-tool/10.0.8/  
**GitHub Tag**: v10.0.8

## 🔧 Windows Text Rotation Fix

### Problem Resolved
Fixed a Windows-specific issue where rotated text positioned near the top edge of images was getting clipped at the bottom. This particularly affected large rotated text elements like "2025" at 102px font size with 8° rotation positioned at y=20.

### Technical Solution
Implemented intelligent positioning logic that:

1. **Detects Top-Edge Positioning**: Identifies text positioned near the top edge (y < 100 pixels)
2. **Smart Padding Calculation**: 
   - Base padding: 15% of font size (minimum 10px)
   - Angle-aware scaling: Normalized to 45° rotation
   - Formula: `int(max(10, font_size * 0.15) * abs(angle) / 45)`
3. **Directional Adjustment**:
   - **Near top edge**: Moves text DOWN to prevent clipping
   - **Other positions**: Maintains existing upward adjustment
4. **Cross-Platform Compatibility**: Only applies on Windows systems

### Real-World Impact
- **Before**: "2025" text at y=20 with 8° rotation → bottom characters clipped
- **After**: "2025" text moved to y=22 → complete character rendering
- **Preservation**: All other text positioning remains unchanged

## 📦 Release Process Completed

### ✅ Version Management
- [x] Updated version: `10.0.7` → `10.0.8`
- [x] Updated CHANGELOG.md with detailed fix description
- [x] Built packages: wheel and source distribution

### ✅ Git Operations
- [x] Committed changes with descriptive message
- [x] Created and pushed git tag: `v10.0.8`
- [x] Pushed to GitHub repository

### ✅ PyPI Distribution
- [x] Successfully uploaded to PyPI
- [x] Both wheel and source distributions available
- [x] Package accessible at: https://pypi.org/project/emailer-simple-tool/10.0.8/

## 🧪 Testing Recommendations

### For Windows Users
Test the fix with your specific fusion configuration:
```csv
text,2025,2850:20,102,center,8,Segoe UI,bold,#ffffff
```

### Expected Results
- Complete rendering of rotated text near top edges
- No bottom character clipping
- Consistent behavior with other platforms
- No impact on non-rotated text or text positioned away from edges

## 📋 Installation

### Upgrade Existing Installation
```bash
pip install --upgrade emailer-simple-tool
```

### Fresh Installation
```bash
# CLI only
pip install emailer-simple-tool

# With GUI support
pip install emailer-simple-tool[gui]
```

### Verify Installation
```bash
emailer-simple-tool --version
# Should output: 10.0.8
```

## 🔄 Next Steps

This release specifically addresses the Windows rotation clipping issue. Future development will continue with:
- Feature Step 10 implementation (Complete French localization)
- Send report parsing improvements
- Additional GUI enhancements

---

**Release Manager**: Amazon Q  
**Automated Release Process**: ✅ Complete
