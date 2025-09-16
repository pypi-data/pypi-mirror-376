import os, shelve, json, gc, weakref, mmap
from itertools import chain
from collections import deque

class DOMM:
    def __init__(self, mem_name="DATAI", dir_path="dearning/memory"):
        self.dir_path = dir_path
        self.base_name = mem_name
        os.makedirs(self.dir_path, exist_ok=True)

        # Path file
        self.shelve_file = os.path.join(self.dir_path, self.base_name + ".db")
        self.json_file = os.path.join(self.dir_path, self.base_name + ".json")
        self.script_file = os.path.join(self.dir_path, self.base_name + ".py")

        # Inisialisasi database
        self.shelf = shelve.open(self.shelve_file)
        deque(maxlen=1000)
        self.experiences = []
        if os.path.exists(self.json_file):
            with open(self.json_file, "r") as f:
                try:
                    self.experiences = json.load(f)
                except:
                    self.experiences = []

        # Buat DATAI.py jika belum ada
        if not os.path.exists(self.script_file):
            with open(self.script_file, "w") as f:
                f.write("# File memory AI: {}\nDATA = {}".format(self.base_name, {}))

    # === Cek ukuran file (max 10MB)
    def check_size(self):
        total = sum(os.path.getsize(f) for f in 
            chain([self.shelve_file, self.json_file, self.script_file]) 
            if os.path.exists(f))
        return total <= 10 * 1024 * 1024  # <= 10MB

    # === Fungsi untuk menyimpan model ke shelve
    def save(self, key, data):
        if not self.check_size():
            raise Exception("Ukuran file memory melebihi 10MB.")
        self.shelf[key] = data
        self.shelf.sync()

    def load(self, key):
        self._cache = weakref.WeakValueDictionary()
        return self.shelf.get(key, None)

    def delete(self, key):
        if key in self.shelf:
            del self.shelf[key]

    def clear(self):
        self.shelf.clear()
        gc.collect()

    # === Fungsi untuk pengalaman (JSON murni)
    def add_experience(self, state, action, reward):
        if not self.check_size():
            raise Exception("Ukuran file memory melebihi 10MB.")
        self.experiences.append({"state": state, "action": action, "reward": reward})
        with open(self.json_file, "r+b") as f:
            mm = mmap.mmap(f.fileno(), 0)
            data = json.loads(mm.read().decode())
            data.append(self.experiences[-1])   # tambahkan 1 data
            mm.seek(0)
            mm.write(json.dumps(data).encode())
            mm.flush()
            mm.close()

    def search_experience(self, min_reward=0.0):
        return [exp for exp in self.experiences if exp["reward"] >= min_reward]

    def clear_experience(self):
        self.experiences = []
        with open(self.json_file, "w") as f:
            json.dump(self.experiences, f)
        gc.collect()

    # === Fungsi untuk menyimpan data manual ke DATAI.py
    def dump_to_script(self):
        with open(self.script_file, "w") as f:
            combined_data = {
                "shelve": dict(self.shelf),
                "experience": self.experiences
            }
            f.write("# Memory export file\n")
            f.write("DATA = ")
            json.dump(combined_data, f, indent=4)

    # === Fungsi untuk membuat file baru dengan nama custom
    def add_memory(self, name):
        new_path = os.path.join(self.dir_path, name + ".py")
        if os.path.exists(new_path):
            return "File sudah ada!"
        with open(new_path, "w") as f:
            f.write("# File memory tambahan\nDATA = {}")
        return "File memory baru berhasil dibuat: " + name + ".py"

    # === Tutup database
    def close(self):
        self.shelf.close()
