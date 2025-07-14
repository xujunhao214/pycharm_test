// 引入 CryptoJS 库
const CryptoJS = require('crypto-js');

// 经过 Base64 编码的 AES 加密后的密文
const ciphertext = pm.variables.get("encryption");

// 解密所需的密钥，确保是 32 字节（AES-256 需要 32 字节）
const key = CryptoJS.enc.Utf8.parse('5fghiobv34534cldfgdfgdf2scvcbcfd'); // 32 字节的密钥

// 初始化向量（IV），它必须与加密时使用的 IV 相同
// 假设 IV 已经作为 Base64 编码字符串提供
const iv = CryptoJS.enc.Utf8.parse('iovbjkdhjdfhfndk'); // 16 字节的 IV（在这个示例中我们假设 IV 为 0）

// AES 解密
const decryptedBytes = CryptoJS.AES.decrypt(ciphertext, key, {
    iv: iv,                      // CBC 模式需要传入 IV
    mode: CryptoJS.mode.CBC,     // CBC 模式
    padding: CryptoJS.pad.Pkcs7  // 填充方式
});

// 将解密后的字节数组转换为 UTF-8 字符串
const originalText = decryptedBytes.toString(CryptoJS.enc.Utf8);

// 输出解密后的文本
console.log(originalText); // 输出解密后的文本
pm.variables.set("decode", originalText);

// 引入 CryptoJS 库
const CryptoJS = require('crypto-js');

// 明文数据
const plaintext = pm.variables.get("decode");

// 解密所需的密钥，确保是 32 字节（AES-256 需要 32 字节）
const key = CryptoJS.enc.Utf8.parse('5fghiobv34534cldfgdfgdf2scvcbcfd'); // 32 字节的密钥

// 生成随机的初始化向量（IV）
const iv = CryptoJS.enc.Utf8.parse('iovbjkdhjdfhfndk'); // 16 字节的 IV（在这个示例中我们假设 IV 为 0）

// AES 加密
const ciphertext = CryptoJS.AES.encrypt(plaintext, key, {
    iv: iv,                      // CBC 模式需要传入 IV
    mode: CryptoJS.mode.CBC,     // CBC 模式
    padding: CryptoJS.pad.Pkcs7  // 填充方式
});

// 输出加密后的密文（Base64 编码）
console.log("Ciphertext (Base64): " + ciphertext.toString());
pm.variables.set("encryption", ciphertext.toString());