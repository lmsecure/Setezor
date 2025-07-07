updateContent();
document.querySelectorAll('.language-option').forEach(option => {
    option.addEventListener('click', function(e) {
        e.preventDefault();
        const selectedLanguage = this.getAttribute('data-value');
        document.getElementById('currentLanguage').textContent = selectedLanguage.toUpperCase();
        
        i18next.changeLanguage(selectedLanguage).then(() => {
            localStorage.setItem('selectedLanguage', selectedLanguage);
            updateContent();
            if (window.location.pathname === '/project_dashboard'){
                get_device_types();
                get_ports_and_protocols();
                get_products_and_service_name();
            }
            if (window.location.pathname === '/vulnerabilities'){
                l4_resources_table.dataLoader.reloadData()
                func_reload_data_update()
            }
            if (window.location.pathname === '/scopes'){
                getScopes()
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('currentLanguage').textContent = savedLanguage.toUpperCase();
});