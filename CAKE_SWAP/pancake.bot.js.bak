const puppeteer = require('puppeteer'); // import Puppeteer

// Path to the actual extension we want to be testing
const pathToExtension = '/Users/nelsonrios/Library/Application\ Support/Google/Chrome/Default/Extensions/nkbihfbeogaeaoehlefnkodbefgpgknn/10.0.2_0'

// Tell puppeteer we want to load the web extension
const puppeteerArgs = [
  `--disable-extensions-except=${pathToExtension}`,
  `--load-extension=${pathToExtension}`,
  '--show-component-extension-options',
];

var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
  return new (P || (P = Promise))(function (resolve, reject) {
    function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
    function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
    function step(result) { result.done ? resolve(result.value) : new P(function (resolve) { resolve(result.value); }).then(fulfilled, rejected); }
    step((generator = generator.apply(thisArg, _arguments || [])).next());
  });
};

function closeHomeScreen(browser) {
  return __awaiter(this, void 0, void 0, function* () {
    return new Promise((resolve, reject) => {
      browser.on('targetcreated', (target) => __awaiter(this, void 0, void 0, function* () {
        if (target.url().match("chrome-extension://[a-z]+/home.html")) {
          try {
            const page = yield target.page();
            resolve(page);
          }
          catch (e) {
            reject(e);
          }
        }
      }));
    });
  });
}

function confirmWelcomeScreen(metamaskPage) {
  return __awaiter(this, void 0, void 0, function* () {
    const continueButton = yield metamaskPage.waitForSelector('.welcome-page button');
    yield continueButton.click();
  });
}

(async () => {
  browser = await puppeteer.launch({
    headless: false,
    // slowMo: 10,
    devtools: true,
    args: puppeteerArgs
  });

  // METAMASK CONFIG FLOW
  const metamaskPage = await closeHomeScreen(browser);
  await confirmWelcomeScreen(metamaskPage);
  const importWalletButton = await metamaskPage.waitForSelector('.first-time-flow__button');
  await importWalletButton.click()
  const noThanksButton = await metamaskPage.waitForSelector('.page-container__footer-button');
  await noThanksButton.click()
  await metamaskPage.waitForSelector('input');
  // TODO use env for password
  await metamaskPage.type('input', '');
  await metamaskPage.type('#password', 'pass1234');
  await metamaskPage.type('#confirm-password', 'pass1234');
  await metamaskPage.click('.first-time-flow__terms')
  await metamaskPage.click('button')
  await metamaskPage.waitForSelector('.end-of-flow__emoji')
  await metamaskPage.click('button')
  const closeModalButton = await metamaskPage.waitForSelector('[data-testid="popover-close"]')
  await closeModalButton.click()

  // ADD BSC NETWORK
  const networkButton = await metamaskPage.waitForSelector('.network-display')
  await networkButton.click()
  await metamaskPage.waitForSelector('li.dropdown-menu-item');
  const networkIndex = await metamaskPage.evaluate(network => {
    const elements = document.querySelectorAll('li.dropdown-menu-item');
    for (let i = 0; i < elements.length; i++) {
      const element = elements[i];
      if (element.innerText.toLowerCase().includes(network.toLowerCase())) {
        return i;
      }
    }
    return elements.length - 1;
  }, 'Custom RPC');
  const customRPCButton = (await metamaskPage.$$('li.dropdown-menu-item'))[networkIndex];
  await customRPCButton.click();
  await metamaskPage.waitForSelector('#network-name')
  await metamaskPage.type('#network-name', 'BSC Mainnet');
  await metamaskPage.type('#rpc-url', 'https://bsc-dataseed.binance.org/');
  await metamaskPage.type('#chainId', '56');
  await metamaskPage.type('#network-ticker', 'BNB');

  const saveNetworkButton = (await metamaskPage.$$('.btn-secondary'))[1];
  await saveNetworkButton.click();

  // OPERATE ON PANCAKESWAP
  // Connect wallet
  const pancakeSwapPage = await browser.newPage();
  await pancakeSwapPage.goto('https://pancakeswap.finance/');
  pancakeSwapPage.waitForNavigation({ waitUntil: 'networkidle0' });

  const [connectWalletButton] = await pancakeSwapPage.$x("//button[contains(., 'Connect Wallet')]");

  await connectWalletButton.click();
  const metamaskButton = await pancakeSwapPage.waitForSelector('#wallet-connect-metamask');
  await metamaskButton.click();

  const newPagePromise = new Promise(x => browser.once('targetcreated', target => x(target.page())));
  const popup = await newPagePromise;

  const nextButton = await popup.waitForSelector('button.btn-primary');
  await nextButton.click();

  const connectButton = await popup.waitForSelector('button.btn-primary.page-container__footer-button');
  await connectButton.click();

  // Harvest all 2 farms
  // const harvestAllButton = await pancakeSwapPage.waitForSelector('#harvest-all');
  // await harvestAllButton.click();

  // const confirmationpagePromise = new Promise(x => browser.once('targetcreated', target => x(target.page())));
  // const confirmationPage = await confirmationpagePromise;

  // const confirmButton = await confirmationPage.waitForSelector('[data-testid="page-container-footer-next"]');

  // await confirmButton.click();

  // const newPagePromise2 = new Promise(x => browser.once('targetcreated', target => x(target.page())));
  // const popup = await newPagePromise2;
  // const confirmButton = await confirmationPage.waitForSelector('[data-testid="page-container-footer-next"]');

  // await confirmButton.click();

  // TODO, wait for div with content: your cake savings have been sent to your wallet

  // Stake harvested cake
  // await pancakeSwapPage.goto('https://pancakeswap.finance/pools');
  // await pancakeSwapPage.setDefaultTimeout(90000);

  // const firstPoolButton = (await pancakeSwapPage.$$('[role="row"]'))[0];
  // await firstPoolButton.click();

  // const addCakeButton = await pancakeSwapPage.waitForSelector('.sc-hKFxyN.jRWmGv.sc-eCApnc.fAYopv');
  // await addCakeButton.click();

  // const [maxCakeButton] = await pancakeSwapPage.$x("//button[contains(., 'Max')]");
  // await maxCakeButton.click();

  // const [confirmStakeButton] = await pancakeSwapPage.$x("//button[contains(., 'Confirm')]");
  // await confirmStakeButton.click();

  // const confirmationStakePagePromise = new Promise(x => browser.once('targetcreated', target => x(target.page())));
  // const confirmationStakePage = await confirmationStakePagePromise;

  // const confirmStakeTransactionButton = await confirmationStakePage.waitForSelector('[data-testid="page-container-footer-next"]');

  // await confirmStakeTransactionButton.click();
  // await pancakeSwapPage.waitForSelector('p.sc-gtsrHT MlLjM');

  // console.log('Cake staked successfully'); // Replace with logger

  // await browser.close();
})();
