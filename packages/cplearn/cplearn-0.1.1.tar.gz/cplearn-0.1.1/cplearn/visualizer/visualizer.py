from .viz_utils import  detailed_viewer, save_coremap_html

class Visualizer:
    def __init__(
            self,
            corespect=None,
            labels=None,
            global_init_embedding=None,
            mode='three_steps'
    ):

        self.corespect = corespect
        self.labels = labels
        self.global_init_embedding = global_init_embedding
        self.mode = mode
        self.fig=detailed_viewer(corespect, self.labels, self.global_init_embedding,self.mode)



    def save_fig(self, filename="coremap_visualization.html"):
        save_coremap_html(self.fig, filename)


