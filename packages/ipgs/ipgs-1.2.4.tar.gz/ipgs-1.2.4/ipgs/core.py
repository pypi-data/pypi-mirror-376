import time, uuid
from IPython.display import display, HTML, Javascript
import numpy as np

class iPgs:
    """
    Fully Flexible Interactive Progress Bar for Jupyter/Colab

    Features:
    - Single loop or nested loop with batches
    - Smooth animated (fill) progress bar
    - Automatic ETA calculation
    - Supports any iterable: list, range, DataLoader-style, tuple/list batches
    - Works even if iterable indices are repeated or variable length

    Args:
        iterable (iterable, optional): Main iterable or batch loader
        num_epochs (int, optional): Number of epochs (default=1)
        desc (str): Description for outer progress bar
        smooth_steps (int): Number of intermediate steps for smooth animation (default=5)
        sleep_time (float): Delay between smooth steps in seconds (default=0.02)
    """

    def __init__(self, iterable=None, num_epochs=1, desc="Processing", smooth_steps=5, sleep_time=0.02):
        self.iterable = iterable
        self.num_epochs = num_epochs
        self.desc = desc
        self.smooth_steps = smooth_steps
        self.sleep_time = sleep_time

        self.use_batches = iterable is not None
        self.num_samples = None
        self.batch_size = 1
        if self.use_batches:
            try:
                self.num_samples = len(getattr(iterable, "dataset", iterable))
            except:
                try:
                    self.num_samples = sum(1 for _ in iterable)
                except:
                    self.num_samples = None
            try:
                first_batch = next(iter(iterable))
                if isinstance(first_batch, (tuple, list)):
                    self.batch_size = len(first_batch[0])
                else:
                    self.batch_size = len(first_batch)
            except:
                self.batch_size = 1

        self.sample_count = 0
        self.start_time = None
        self.prev_outer_percent = 0
        self.prev_inner_percent = 0

        # HTML IDs
        self.outer_bar_id = f"bar_outer_{uuid.uuid4().hex}"
        self.outer_text_id = f"text_outer_{uuid.uuid4().hex}"
        self.outer_eta_id = f"eta_outer_{uuid.uuid4().hex}"
        self.inner_bar_id = f"bar_inner_{uuid.uuid4().hex}"
        self.inner_text_id = f"text_inner_{uuid.uuid4().hex}"
        self.inner_eta_id = f"eta_inner_{uuid.uuid4().hex}"

        self._display_html()

    def _display_html(self):
        html = f"""
        <div style="width:600px; font-family:sans-serif; margin:10px 0;">
            <!-- Outer Progress -->
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <strong>{self.desc}</strong>
                <span id="{self.outer_text_id}">0/-- (0.0%)</span>
            </div>
            <div style="height:16px; background:#eee; border-radius:999px; overflow:hidden; border:1px solid #ddd; margin-bottom:12px;">
                <div id="{self.outer_bar_id}" style="
                    height:100%; width:0%; 
                    background:linear-gradient(90deg,#0072ff,#00c6ff); 
                    border-radius:999px; display:flex; align-items:center; justify-content:center; 
                    color:white; font-size:11px; 
                    transition: width 0.3s ease;">
                    <span>0.0%</span>
                </div>
            </div>
            <div style="margin-bottom:20px; display:flex; justify-content:flex-end;">
                <span id="{self.outer_eta_id}" style="
                    font-size:12px; background:#f8f9fa; border:1px solid #ddd; 
                    border-radius:6px; padding:2px 8px; color:#333;">ETA: --:--</span>
            </div>
        """
        if self.use_batches:
            html += f"""
            <!-- Inner Progress -->
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <strong>Batch</strong>
                <span id="{self.inner_text_id}">0/-- (0.0%)</span>
            </div>
            <div style="height:12px; background:#f0f0f0; border-radius:999px; overflow:hidden; border:1px solid #ddd;">
                <div id="{self.inner_bar_id}" style="
                    height:100%; width:0%; 
                    background:linear-gradient(90deg,#ff5722,#ff9800); 
                    border-radius:999px; display:flex; align-items:center; justify-content:center; 
                    color:white; font-size:10px; 
                    transition: width 0.3s ease;">
                    <span>0.0%</span>
                </div>
            </div>
            <div style="margin-top:4px; display:flex; justify-content:flex-end;">
                <span id="{self.inner_eta_id}" style="
                    font-size:11px; background:#f8f9fa; border:1px solid #ddd; 
                    border-radius:6px; padding:2px 6px; color:#333;">ETA: --:--</span>
            </div>
            """
        html += "</div>"
        display(HTML(html))

    def start_timer(self):
        self.start_time = time.time()

    def _smooth_update(self, element, prev, new, text=None, eta=None):
        for val in np.linspace(prev, new, self.smooth_steps):
            js = f"""
            (function(){{
                var b=document.getElementById('{element[0]}');
                var t=document.getElementById('{element[1]}');
                var e=document.getElementById('{element[2]}');
                if(b){{b.style.width='{val:.2f}%'; b.querySelector('span').textContent='{val:.1f}%';}}
                if(t && '{text}'!='None') t.textContent='{text}';
                if(e && '{eta}'!='None') e.textContent='{eta}';
            }})();
            """
            display(Javascript(js))
            time.sleep(self.sleep_time)
        return new

    def __iter__(self):
        self.start_timer()
        if self.use_batches:
            for epoch_idx in range(self.num_epochs):
                num_batches = len(self.iterable)
                for batch_idx, batch in enumerate(self.iterable, 1):
                    if not isinstance(batch, (tuple, list)):
                        batch = (batch,)
                    try:
                        self.sample_count += len(batch[0])
                    except TypeError:
                        self.sample_count += 1

                    elapsed = time.time() - self.start_time
                    total_samples = self.num_samples * self.num_epochs if self.num_samples else 1
                    percent_outer = (self.sample_count / total_samples) * 100
                    remaining_outer = (elapsed / self.sample_count * (total_samples - self.sample_count)) if self.sample_count else 0
                    m,s = divmod(int(remaining_outer),60)
                    eta_outer = f"{m:02d}:{s:02d}"

                    percent_inner = (batch_idx / num_batches) * 100
                    remaining_inner = (elapsed / batch_idx * (num_batches - batch_idx)) if batch_idx else 0
                    m2,s2 = divmod(int(remaining_inner),60)
                    eta_inner = f"{m2:02d}:{s2:02d}"

                    self.prev_outer_percent = self._smooth_update(
                        (self.outer_bar_id, self.outer_text_id, self.outer_eta_id),
                        self.prev_outer_percent,
                        percent_outer,
                        text=f"Epoch {epoch_idx+1}/{self.num_epochs} Total {self.sample_count}/{total_samples} ({percent_outer:.1f}%)",
                        eta=eta_outer
                    )
                    self.prev_inner_percent = self._smooth_update(
                        (self.inner_bar_id, self.inner_text_id, self.inner_eta_id),
                        self.prev_inner_percent,
                        percent_inner,
                        text=f"Batch {batch_idx}/{num_batches} ({percent_inner:.1f}%)",
                        eta=eta_inner
                    )
                    yield epoch_idx, batch_idx, batch
        else:
            for idx, item in enumerate(range(self.num_epochs),1):
                self.sample_count += 1
                elapsed = time.time() - self.start_time
                percent_outer = (self.sample_count / self.num_epochs) * 100
                remaining_outer = (elapsed / self.sample_count * (self.num_epochs - self.sample_count)) if self.sample_count else 0
                m,s = divmod(int(remaining_outer),60)
                eta_outer = f"{m:02d}:{s:02d}"

                self.prev_outer_percent = self._smooth_update(
                    (self.outer_bar_id, self.outer_text_id, self.outer_eta_id),
                    self.prev_outer_percent,
                    percent_outer,
                    text=f"{self.sample_count}/{self.num_epochs} ({percent_outer:.1f}%)",
                    eta=eta_outer
                )
                yield idx, (item,)
        self.close()

    def close(self):
        self._smooth_update(
            (self.outer_bar_id, self.outer_text_id, self.outer_eta_id),
            self.prev_outer_percent, 100,
            text="Done..!", eta="Elapsed ✔"
        )
        if self.use_batches:
            self._smooth_update(
                (self.inner_bar_id, self.inner_text_id, self.inner_eta_id),
                self.prev_inner_percent, 100,
                text="Batch Done..!", eta="Elapsed ✔"
            )
