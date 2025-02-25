import xarray as xr


class TopoTemplates:
    
    def __init__(self):
    # def __init__(self, template_fnames: list, rois: list, phases: list):
        
        # self.template_fnames = template_fnames
        # self.rois = rois
        # self.phases = phases
        return
    
    
    def load_templates(self, topo_fname: str):
        
        topographies = xr.load_dataarray(topo_fname)
        
        templates = {}
        for roi in topographies.rois:
            roi = str(roi.values)
            templates[roi] = topographies.sel(rois=[roi])
            
        self.templates = templates
        print("Templates loaded.")
        return
    
    
    def del_channels(self, channels: list):
        
        for roi in self.templates.keys():
            self.templates[roi] = self.templates[roi].drop_sel(channels=channels)
        print('Channels', channels, 'deleted.')
        return
    
    
    def select_templates(self, roi: str, phase: str, twin: tuple=(-.025, .0)):
        
        selected_templates = []
        for t in self.templates.keys():
            if roi in t:
                vals = self.templates[t].sel(times=slice(*twin)).mean('times').values.squeeze()
                selected_templates.append([vals, t, phase])
                print("Templates selected: ", selected_templates[-1][1], 
                      selected_templates[-1][-1])
        self.selected_templates = selected_templates
        return selected_templates
