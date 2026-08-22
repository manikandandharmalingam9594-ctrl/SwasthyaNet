with open("src/pages/DistrictAdminDashboard.jsx", "r") as f:
    content = f.read()

if "DistrictMap" not in content:
    content = content.replace(
        "import { \n  Building2,", 
        "import DistrictMap from '../components/DistrictMap';\nimport { \n  Building2,"
    )
    
    # Insert map between Top Metrics and Centre List Table
    content = content.replace(
        "{/* Centre List Table */}", 
        "{/* Interactive Map */}\n        <DistrictMap centres={centres} />\n\n        {/* Centre List Table */}"
    )

    with open("src/pages/DistrictAdminDashboard.jsx", "w") as f:
        f.write(content)
        
    print("Injected DistrictMap into DistrictAdminDashboard.jsx")
