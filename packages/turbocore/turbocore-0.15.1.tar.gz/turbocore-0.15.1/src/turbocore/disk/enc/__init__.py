from turbocore import cli_this
import subprocess
import os


def enc_new(NAME, MB, K):
    diskfile = "%s.img" % NAME
    kfile = "/tmp/tc-disk-enc-K-tmp"
    devfile = "%s.dev" % NAME
    dd_res = subprocess.check_output("""/bin/bash -c 'dd if=/dev/zero of=%s bs=1M count=%d; exit 0' 2>&1""" % (diskfile, int(MB)), shell=True, universal_newlines=True)
    with open(kfile, 'w') as f:
        f.write(K)
    losetup_res = subprocess.check_output("""/bin/bash -c 'losetup --find --show %s' 2>&1""" % (diskfile), shell=True, universal_newlines=True).strip().split("\n")[0].strip()
    with open(devfile, 'w') as f:
        f.write(losetup_res)

    luksFormat_res = subprocess.check_output("""/bin/bash -c 'cryptsetup luksFormat %s %s' 2>&1""" % (losetup_res, kfile), shell=True, universal_newlines=True, input="YES")
    luksOpen_res = subprocess.check_output("""/bin/bash -c 'cryptsetup luksOpen %s %s %s' 2>&1""" % (losetup_res, NAME, kfile), shell=True, universal_newlines=True)
    os.unlink(kfile)
    mkfsext4_res = subprocess.check_output("""/bin/bash -c 'mkfs.ext4 /dev/mapper/%s' 2>&1""" % (NAME), shell=True, universal_newlines=True)
    os.makedirs(NAME, exist_ok=True)
    mount_res = subprocess.check_output("""/bin/bash -c 'mount /dev/mapper/%s %s' 2>&1""" % (NAME, NAME), shell=True, universal_newlines=True)


def enc_open(NAME, K):
    pass


def enc_close(NAME):
    pass


def enc_help():
    print("""How it works:
          
python -m turbocore.disk.enc help
python -m turbocore.disk.enc new   NAME MB K
python -m turbocore.disk.enc open  NAME K
python -m turbocore.disk.enc close NAME
""")


def main():
    cli_this(__name__, 'enc_')
