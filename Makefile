# Read the Docs 中文文档构建入口（GNU make）
PY           ?= python
SPHINX_BUILD ?= sphinx-build
SPHINX_INTL  ?= sphinx-intl
SOURCEDIR    := upstream/docs
LOCALEDIR    := locale
BUILDDIR     := _build
POTDIR       := $(BUILDDIR)/gettext
HTMLDIR      := $(BUILDDIR)/html

.PHONY: help gettext update build preview check clean

help:
	@echo "可用目标："
	@echo "  gettext  从 upstream/docs（由 multiproject 选 user docset）生成 .pot 到 $(POTDIR)"
	@echo "  update   生成 pot 并合并到 $(LOCALEDIR)/zh_CN 的 .po"
	@echo "  build    生成提交元数据、编译 .mo、构建 HTML 到 $(HTMLDIR)"
	@echo "  preview  构建后启动本地实时预览 127.0.0.1:8000"
	@echo "  check    运行全部质量门槛（脚本 scripts/check_translation.sh）"
	@echo "  clean    清理 $(BUILDDIR) 与 _generated"

gettext:
	rm -rf $(POTDIR)
	PROJECT=user $(SPHINX_BUILD) -b gettext -c . $(SOURCEDIR) $(POTDIR)

update: gettext
	$(SPHINX_INTL) update -d $(LOCALEDIR) -p $(POTDIR) -l zh_CN --no-obsolete

build:
	$(PY) scripts/gen_upstream_meta.py
	$(SPHINX_INTL) build -d $(LOCALEDIR) -l zh_CN
	PROJECT=user $(SPHINX_BUILD) -b html -c . -D language=zh_CN $(SOURCEDIR) $(HTMLDIR)

preview: build
	PROJECT=user sphinx-autobuild -c . -D language=zh_CN $(SOURCEDIR) $(HTMLDIR) \
		--host 127.0.0.1 --port 8000

check:
	bash scripts/check_translation.sh

clean:
	rm -rf $(BUILDDIR) _generated
