import xarray as xr


class TopoTemplates:
    
    def __init__(self, template_fnames: list, rois: list, phases: list):
        
        self.template_fnames = template_fnames
        self.rois = rois
        self.phases = phases
        return
    
    
    def load_templates(self):
        
        templates = {}
        for template_fname, roi, phase in zip(self.template_fnames, self.rois, self.phases):
            template = xr.load_dataarray(template_fname).values
            templates[f'{roi}_{phase}'] = template
            
        self.templates = templates
        return
    
    
    def select_templates(self, roi: list, phase: list):
        
        selected_templates = []
        for r, p in zip(roi, phase):
            selected_templates.append([self.templates[f'{r}_{p}'], r, p])
        self.select_templates = selected_templates
        return selected_templates
