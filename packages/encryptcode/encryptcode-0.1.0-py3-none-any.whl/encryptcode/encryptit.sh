# DEFINE TEMP DIR
tmp="/tmp/encode"

# CREATE TEMP DIR
mkdir -p $tmp

# DEFINE ENCRYPTCODE PATH"
path=$(python -c "import sysconfig; print('%s/encryptcode' %sysconfig.get_paths().get('purelib'))")

# COPY PYX FROM LIB TO TEMP DIR"
cp -rf $path/*.py $tmp/.

# ADD CRYPTO KEY"
python $tmp/encryptcode.py --addkey --file $tmp/encryptcode.py

# ENCRYPT THE CODE BASE"
python $tmp/encryptcode.py --encrypt --path $1

# COMPILE AND BUILD"
python $tmp/setup.py build_ext --inplace

# MOVE COMPILED .so FILE TO LIB"
mv $tmp/encryptcode*.so $path/.

# CLEANUP"
rm -rf $tmp
