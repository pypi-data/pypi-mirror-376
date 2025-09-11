import time, uuid
from IPython.display import display, HTML, Javascript

class iPgs:
    """
    iPgs: Interactive Animated Progress Bar for Jupyter/Colab

    Framework-agnostic: works with PyTorch, TensorFlow, Keras, NumPy arrays, lists, or any iterable.

    Yields:
        epoch_idx (int): current epoch index (0-based)
        batch_idx (int): current batch index (1-based)
        batch (tuple or single object): batch data; if batch is a single object, returned as (batch,)

    Features:
    - Nested progress bars: epoch-level (outer) and batch-level (inner)
    - Smooth animated, live visualization in Jupyter/Colab
    - Automatic ETA calculation for both epoch and batch
    - Works with standard Python iterables or DataLoader-style iterables
    - No external dependencies (dependency-free)

    Usage Example:
        for epoch_idx, batch_idx, batch in iPgs(loader, num_epochs=5, desc="Training"):
            bx, by = batch  # works with single or tuple batches
            ...
    """
    
    def __init__(self, loader, num_epochs=1, desc="Training"):
        self.loader = loader
        self.num_epochs = num_epochs
        self.desc = desc

        # Detect number of samples if possible
        try:
            self.num_samples = len(loader.dataset)
        except:
            try:
                self.num_samples = sum(1 for _ in loader)
            except:
                self.num_samples = None

        # Detect batch size if possible
        try:
            first_batch = next(iter(loader))
            if isinstance(first_batch, (tuple, list)):
                self.batch_size = len(first_batch[0])
            else:
                self.batch_size = len(first_batch)
        except:
            self.batch_size = 1

        self.sample_count = 0
        self.start_time = None

        # Unique HTML ids for progress bars
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
        </div>
        """
        display(HTML(html))

    def start_timer(self):
        self.start_time = time.time()

    def _update_bar(self, outer_percent=None, outer_text=None, outer_eta=None,
                    inner_percent=None, inner_text=None, inner_eta=None):
        js = ""
        if outer_percent is not None:
            js += f"""
            (function(){{
                var b=document.getElementById('{self.outer_bar_id}');
                var t=document.getElementById('{self.outer_text_id}');
                var e=document.getElementById('{self.outer_eta_id}');
                if(b){{b.style.width='{outer_percent:.2f}%'; b.querySelector('span').textContent='{outer_percent:.1f}%';}}
                if(t && '{outer_text}'!='None') t.textContent='{outer_text}';
                if(e && '{outer_eta}'!='None') e.textContent='{outer_eta}';
            }})();
            """
        if inner_percent is not None:
            js += f"""
            (function(){{
                var b=document.getElementById('{self.inner_bar_id}');
                var t=document.getElementById('{self.inner_text_id}');
                var e=document.getElementById('{self.inner_eta_id}');
                if(b){{b.style.width='{inner_percent:.2f}%'; b.querySelector('span').textContent='{inner_percent:.1f}%';}}
                if(t && '{inner_text}'!='None') t.textContent='{inner_text}';
                if(e && '{inner_eta}'!='None') e.textContent='{inner_eta}';
            }})();
            """
        display(Javascript(js))

    def __iter__(self):
        self.start_timer()
        for epoch_idx in range(self.num_epochs):
            num_batches = len(self.loader)
            for batch_idx, batch in enumerate(self.loader, 1):
                # Ensure batch is tuple
                if not isinstance(batch, (tuple, list)):
                    batch = (batch,)

                # Update sample count (framework-agnostic)
                try:
                    self.sample_count += len(batch[0])
                except TypeError:
                    self.sample_count += 1

                # Time and ETA calculation
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

                self._update_bar(
                    outer_percent=percent_outer,
                    outer_text=f"Epoch {epoch_idx+1}/{self.num_epochs} Total {self.sample_count}/{total_samples} ({percent_outer:.1f}%)",
                    outer_eta=eta_outer,
                    inner_percent=percent_inner,
                    inner_text=f"Batch {batch_idx}/{num_batches} ({percent_inner:.1f}%)",
                    inner_eta=eta_inner
                )

                yield epoch_idx, batch_idx, batch

        self.close()

    def close(self):
        self._update_bar(
            outer_percent=100, inner_percent=100,
            outer_text="Done..!", inner_text="Batch Processing Done..!",
            outer_eta="Elapsed ✔", inner_eta="Elapsed ✔"
        )
