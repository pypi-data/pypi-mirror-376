import time, uuid
from IPython.display import display, HTML, Javascript
import math

class iPgs:
    """
    Nested Progress Bar for epochs + batches
    - Auto-detect samples & batch size if DataLoader given
    - Can also work with manual loops (advanced users)
    """

    def __init__(self, loader=None, num_epochs=1, desc="Training"):
        """
        loader: iterable (e.g., PyTorch DataLoader) or None
        num_epochs: total epochs
        desc: description text
        """
        self.loader = loader
        self.num_epochs = num_epochs
        self.desc = desc

        # Auto detect num_samples & batch_size
        if loader is None:
            self.num_samples = None
            self.batch_size = None
            self.loader_iterable = None
        elif isinstance(loader, int):
            self.num_samples = loader
            self.batch_size = 1
            self.loader_iterable = None
        else:
            try:
                self.num_samples = len(loader.dataset)
            except AttributeError:
                try:
                    self.num_samples = len(loader)
                except TypeError:
                    self.num_samples = sum(1 for _ in loader)
            try:
                first_batch = next(iter(loader))
                if isinstance(first_batch, (tuple, list)):
                    self.batch_size = len(first_batch[0])
                else:
                    self.batch_size = len(first_batch)
            except Exception:
                self.batch_size = 1
            self.loader_iterable = loader

        # Progress tracking
        self.sample_count = 0
        self.start_time = None

        # unique IDs for HTML elements
        self.outer_bar_id = f"bar_outer_{uuid.uuid4().hex}"
        self.outer_text_id = f"text_outer_{uuid.uuid4().hex}"
        self.outer_eta_id = f"eta_outer_{uuid.uuid4().hex}"

        self.inner_bar_id = f"bar_inner_{uuid.uuid4().hex}"
        self.inner_text_id = f"text_inner_{uuid.uuid4().hex}"
        self.inner_eta_id = f"eta_inner_{uuid.uuid4().hex}"

        self._display_html()

    def _display_html(self):
        html = f"""
        <div style="width:600px; font-family:'Segoe UI',Tahoma,Arial; margin:10px 0;">
          <!-- Outer: total progress -->
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <strong style="font-size:14px">{self.desc}</strong>
            <span id="{self.outer_text_id}" style="font-size:13px; color:#222">0/-- (0.0%)</span>
          </div>
          <div style="height:16px; background:#eee; border-radius:999px; overflow:hidden; border:1px solid #ddd; margin-bottom:12px;">
            <div id="{self.outer_bar_id}" style="
                height:100%;
                width:0%;
                background:linear-gradient(90deg,#0072ff,#00c6ff);
                border-radius:999px;
                transition: width 0.45s;
                display:flex; align-items:center; justify-content:center;
                color:white; font-size:11px;">
              <span style="padding:0 6px; white-space:nowrap;">0.0%</span>
            </div>
          </div>
          <div style="margin-bottom:20px; display:flex; justify-content:flex-end;">
            <span id="{self.outer_eta_id}" style="
                font-size:12px;
                background:#f8f9fa;
                border:1px solid #ddd;
                border-radius:6px;
                padding:2px 8px;
                color:#333;
                box-shadow:0 1px 2px rgba(0,0,0,0.1);
                font-family:'Consolas','Courier New',monospace;">
              ETA: --:--
            </span>
          </div>

          <!-- Inner: batch progress -->
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <strong style="font-size:13px">Batch</strong>
            <span id="{self.inner_text_id}" style="font-size:12px; color:#222">0/-- (0.0%)</span>
          </div>
          <div style="height:12px; background:#f0f0f0; border-radius:999px; overflow:hidden; border:1px solid #ddd;">
            <div id="{self.inner_bar_id}" style="
                height:100%;
                width:0%;
                background:linear-gradient(90deg,#ff5722,#ff9800);
                border-radius:999px;
                transition: width 0.35s;
                display:flex; align-items:center; justify-content:center;
                color:white; font-size:10px;">
              <span style="padding:0 4px; white-space:nowrap;">0.0%</span>
            </div>
          </div>
          <div style="margin-top:4px; display:flex; justify-content:flex-end;">
            <span id="{self.inner_eta_id}" style="
                font-size:11px;
                background:#f8f9fa;
                border:1px solid #ddd;
                border-radius:6px;
                padding:2px 6px;
                color:#333;
                box-shadow:0 1px 2px rgba(0,0,0,0.1);
                font-family:'Consolas','Courier New',monospace;">
              ETA: --:--
            </span>
          </div>
        </div>
        """
        display(HTML(html))

    def update(self, processed_samples=1, batch_idx=None, num_batches=None, epoch_idx=None, total_samples=None):
        """
        Manual update: can be called inside user's nested loops
        processed_samples: number of samples processed in this step
        batch_idx / num_batches: current batch info
        epoch_idx / total_samples: optional for more precise display
        """
        self.sample_count += processed_samples
        self._update_outer(total_samples)
        self._update_inner(batch_idx, num_batches)

    def _update_outer(self, total_samples=None):
        total_samples = total_samples or (self.num_samples * self.num_epochs if self.num_samples else 1)
        percent = (self.sample_count / total_samples) * 100
        elapsed = time.time() - self.start_time if self.start_time else 1
        remaining = (elapsed / self.sample_count * (total_samples - self.sample_count)) if self.sample_count else 0
        m, s = divmod(int(remaining), 60)
        eta_str = f"{m:02d}:{s:02d}"
        js = f"""
        (function(){{
            var b = document.getElementById('{self.outer_bar_id}');
            var t = document.getElementById('{self.outer_text_id}');
            var e = document.getElementById('{self.outer_eta_id}');
            if(b) {{ b.style.width = '{percent:.2f}%'; b.querySelector('span').textContent='{percent:.1f}%'; }}
            if(t) t.textContent='Total {self.sample_count}/{total_samples} ({percent:.1f}%)';
            if(e) e.textContent='ETA: {eta_str}';
        }})();
        """
        display(Javascript(js))

    def _update_inner(self, batch_idx, num_batches):
        if batch_idx is None or num_batches is None: return
        percent = (batch_idx / num_batches) * 100
        elapsed = time.time() - self.start_time if self.start_time else 1
        remaining = (elapsed / batch_idx * (num_batches - batch_idx)) if batch_idx else 0
        m, s = divmod(int(remaining), 60)
        eta_str = f"{m:02d}:{s:02d}"
        js = f"""
        (function(){{
            var b = document.getElementById('{self.inner_bar_id}');
            var t = document.getElementById('{self.inner_text_id}');
            var e = document.getElementById('{self.inner_eta_id}');
            if(b) {{ b.style.width = '{percent:.2f}%'; b.querySelector('span').textContent='{percent:.1f}%'; }}
            if(t) t.textContent='Batch {batch_idx}/{num_batches} ({percent:.1f}%)';
            if(e) e.textContent='ETA: {eta_str}';
        }})();
        """
        display(Javascript(js))

    def start_timer(self):
        self.start_time = time.time()

    def close(self):
        js = f"""
        (function(){{
            var ob = document.getElementById('{self.outer_bar_id}');
            var ib = document.getElementById('{self.inner_bar_id}');
            var ot = document.getElementById('{self.outer_text_id}');
            var it = document.getElementById('{self.inner_text_id}');
            var oe = document.getElementById('{self.outer_eta_id}');
            var ie = document.getElementById('{self.inner_eta_id}');
            if(ob) {{ ob.style.width='100%'; ob.style.background='#2e7d32'; ob.querySelector('span').textContent='100%'; }}
            if(ib) {{ ib.style.width='100%'; ib.style.background='#4caf50'; ib.querySelector('span').textContent='100%'; }}
            if(ot) ot.textContent='✅ Done..!';
            if(it) it.textContent='✅ Batch Done..!';
            if(oe) oe.textContent='Elapsed ✔';
            if(ie) ie.textContent='Elapsed ✔';
        }})();
        """
        display(Javascript(js))
