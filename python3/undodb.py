import os
import sqlite3
import tempfile
import vim

IGNORE_EXTS = {'.txt'}

conn = sqlite3.connect(os.path.join(vim.eval('$VIMFILES'), 'undo.sqlite'))
curr = conn.cursor()
curr.execute('pragma synchronous = off')
curr.execute('pragma journal_mode = wal')
curr.execute('create table if not exists undo (f text not null primary key, u blob)')

class Undofile:
    def __enter__(self):
        self.temp = tempfile.NamedTemporaryFile(delete=False)
        self.temp.close()
        # wundo will fail if the file exists
        os.unlink(self.temp.name)
        return self.temp.name

    def __exit__(self, exc_type, exc_value, traceback):
        if os.path.isfile(self.temp.name):
            os.unlink(self.temp.name)

def skipped():
    if vim.eval('&modifiable') == '0':
        return True

    bufpath = vim.current.buffer.name
    if bufpath is None or bufpath == '':
        return True

    ext = os.path.splitext(bufpath)[1].lower()
    if ext in IGNORE_EXTS:
        return True

    return False

def write():
    if skipped():
        return
    bufpath = vim.current.buffer.name.lower()
    with Undofile() as temp:
        vim.command('wundo {}'.format(temp))

        if not os.path.isfile(temp) or os.path.getsize(temp) == 0:
            return

        curr.execute('select 1 from undo where f = ?', (bufpath, ))
        with open(temp, 'rb') as f:
            if curr.fetchone():
                curr.execute('update undo set u = ? where f = ?', (f.read(), bufpath))
            else:
                curr.execute('insert into undo values (?, ?)', (bufpath, f.read()))
        conn.commit()

def read():
    if skipped():
        return
    bufpath = vim.current.buffer.name.lower()
    with Undofile() as temp:
        curr.execute('select u from undo where f = ?', (bufpath, ))
        row = curr.fetchone()
        if row:
            with open(temp, 'wb') as f:
                f.write(row[0])
            vim.command('rundo {}'.format(temp))
