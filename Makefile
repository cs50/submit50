MAINTAINER = "CS50 <sysadmins@cs50.harvard.edu>"
NAME = submit50
VERSION = 2.1.4

.PHONY: bash
bash:
	docker build -t submit50 .
	docker run -i --rm -v "$(PWD)":/root -t submit50

.PHONY: clean
clean:
	rm -f $(NAME)_$(VERSION)_*.deb
	rm -f $(NAME)-$(VERSION)-*.pkg.tar.xz
	rm -f $(NAME)-$(VERSION)-*.rpm

.PHONY: deb
deb:
	rm -f $(NAME)_$(VERSION)_*.deb
	fpm \
	-m $(MAINTAINER) \
	-n $(NAME) \
	-s dir \
	-t deb \
	-v $(VERSION) \
	--after-install after-install.sh \
	--after-remove after-remove.sh \
	--deb-no-default-config-files \
	--depends git \
    --depends python3 \
	--depends python3-pexpect \
	--depends python3-termcolor \
	opt

# TODO: add dependencies
.PHONY: pacman
pacman:
	rm -f $(NAME)-$(VERSION)-*.pkg.tar.xz
	fpm \
	-m $(MAINTAINER) \
	-n $(NAME) \
	-s dir \
	-t pacman \
	-v $(VERSION) \
	--after-install after-install.sh \
	--after-remove after-remove.sh \
	opt


# TODO: add dependencies
.PHONY: rpm
rpm:
	rm -f $(NAME)-$(VERSION)-*.rpm
	fpm \
	-m $(MAINTAINER) \
	-n $(NAME) \
	-s dir \
	-t rpm \
	-v $(VERSION) \
	--after-install after-install.sh \
	--after-remove after-remove.sh \
	opt
