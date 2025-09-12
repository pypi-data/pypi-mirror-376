import time
import uuid
from IPython.display import display, HTML, Javascript
import numpy as np

class iPgs:
    """
    Fully Flexible Interactive Progress Bar for Jupyter/Colab Notebooks.

    This class allows for easy creation of progress bars for single or nested loops
    with corrected timing for nested updates and color customization.

    Args:
        iterable (iterable or int): The main iterable (e.g., list, range, DataLoader) 
                                     or an integer representing the total number of steps.
        desc (str, optional): A description for the progress bar. Defaults to "Processing".
        total (int, optional): The total number of items in the iterable. If not provided,
                               the class will attempt to infer it using len().
        color (str, optional): The color theme for the bar. Accepts 'blue' or 'orange'. 
                               Defaults to 'blue'.
        smooth_steps (int, optional): Number of intermediate steps for smooth animation. 
                                      Defaults to 10.
        sleep_time (float, optional): Delay between smooth animation steps in seconds. 
                                      Defaults to 0.01.
    """
    _colors = {
        'blue': 'linear-gradient(90deg, #0b3d91, #0072ff)',    # Dark Blue Gradient
        'orange': 'linear-gradient(90deg, #e64a19, #ff9800)', # Orange-Red Gradient
        'green': 'linear-gradient(90deg, #1e7e34, #28a745)'     # Green for completion
    }

    def __init__(self, iterable, desc="Processing", total=None, color='blue', smooth_steps=10, sleep_time=0.01):
        if isinstance(iterable, int):
            self.total = iterable
            self.iterable = range(iterable)
        else:
            self.iterable = iterable
            if total is None:
                try:
                    self.total = len(iterable)
                except (TypeError, AttributeError):
                    self.total = None
            else:
                self.total = total
        
        self.desc = desc
        self.color = color
        self.smooth_steps = smooth_steps
        self.sleep_time = sleep_time
        
        self.count = 0
        self.start_time = None
        self.prev_percent = 0
        
        # Unique HTML IDs
        self.bar_id = f"pgs-bar-{uuid.uuid4().hex}"
        self.text_id = f"pgs-text-{uuid.uuid4().hex}"
        self.eta_id = f"pgs-eta-{uuid.uuid4().hex}"
        
        self._display_html()

    def _display_html(self):
        """Renders the HTML structure for the progress bar."""
        bar_color = self._colors.get(self.color, self._colors['blue'])
        html = f"""
        <div style="width: 600px; font-family: sans-serif; margin: 10px 0; padding-left: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <strong>{self.desc}</strong>
                <span id="{self.text_id}" style="font-size: 13px;">0/{self.total or '--'} (0.0%)</span>
            </div>
            <div style="height: 16px; background: #eee; border-radius: 999px; overflow: hidden; border: 1px solid #ddd; margin-bottom: 12px;">
                <div id="{self.bar_id}" style="
                    height: 100%; width: 0%;
                    background: {bar_color};
                    border-radius: 999px; display: flex; align-items: center; justify-content: center;
                    color: white; font-size: 11px;
                    transition: width 0.2s ease-in-out;">
                    <span>0.0%</span>
                </div>
            </div>
            <div style="display: flex; justify-content: flex-end;">
                <span id="{self.eta_id}" style="
                    font-size: 12px; background: #f8f9fa; border: 1px solid #ddd;
                    border-radius: 6px; padding: 2px 8px; color: #333;">ETA: --:--</span>
            </div>
        </div>
        """
        display(HTML(html))

    def _update_display(self):
        """Calculates and pushes updates to the frontend."""
        elapsed = time.time() - self.start_time
        
        if self.total and self.total > 0:
            percent = (self.count / self.total) * 100
            text_str = f"{self.count}/{self.total} ({percent:.1f}%)"
            remaining_time = (elapsed / self.count * (self.total - self.count)) if self.count > 0 else 0
            m, s = divmod(int(remaining_time), 60)
            eta_str = f"{m:02d}:{s:02d}"
        else:
            percent = 0
            text_str = f"{self.count}/?"
            items_per_sec = self.count / elapsed if elapsed > 0 else 0
            eta_str = f"{items_per_sec:.2f} it/s"
        
        # Smooth animation via Javascript
        for val in np.linspace(self.prev_percent, percent, self.smooth_steps):
            js = f"""
            (function(){{
                var bar = document.getElementById('{self.bar_id}');
                var text = document.getElementById('{self.text_id}');
                var eta = document.getElementById('{self.eta_id}');
                if(bar) {{
                    bar.style.width = '{val:.2f}%';
                    bar.querySelector('span').textContent = '{val:.1f}%';
                }}
                if(text) text.textContent = '{text_str}';
                if(eta) eta.textContent = 'ETA: {eta_str}';
            }})();
            """
            display(Javascript(js))
            if self.smooth_steps > 1:
                time.sleep(self.sleep_time)
        self.prev_percent = percent

    def __iter__(self):
        self.start_time = time.time()
        iterator = iter(self.iterable)
        
        while True:
            try:
                # Get next item
                item = next(iterator)
                # Yield it to the user's loop first
                yield item
                # After user's code runs, update the progress
                self.count += 1
                self._update_display()
            except StopIteration:
                # The loop has finished
                break
        
        self.close()

    def close(self):
        """Finalizes the progress bar to 100% and shows completion status."""
        elapsed = time.time() - self.start_time
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        total_time_str = f"{h:02d}:{m:02d}:{s:02d}"
        
        final_text = f"{self.count}/{self.total}" if self.total else f"{self.count} items"
        
        js = f"""
        (function(){{
            var bar = document.getElementById('{self.bar_id}');
            var text = document.getElementById('{self.text_id}');
            var eta = document.getElementById('{self.eta_id}');
            if(bar) {{
                bar.style.width = '100%';
                bar.querySelector('span').textContent = '100%';
                bar.style.background = '{self._colors['green']}';
            }}
            if(text) text.textContent = '{final_text}';
            if(eta) eta.textContent = 'Elapsed: {total_time_str} ✔';
        }})();
        """
        display(Javascript(js))
