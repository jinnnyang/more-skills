import { execSync } from 'child_process';
import fs from 'fs';

const code_cn = 'sankey-beta\n"学习总预算","精读",200\n';
const code_cn_noquote = 'sankey-beta\n学习总预算,精读,200\n';

fs.writeFileSync('test_cn.mmd', code_cn);
fs.writeFileSync('test_cn_nq.mmd', code_cn_noquote);

try {
    execSync('node cli.js --validate-only -i test_cn.mmd', {stdio: 'inherit'});
    console.log('test_cn.mmd passed');
} catch(e) {
    console.log('test_cn.mmd failed');
}

try {
    execSync('node cli.js --validate-only -i test_cn_nq.mmd', {stdio: 'inherit'});
    console.log('test_cn_nq.mmd passed');
} catch(e) {
    console.log('test_cn_nq.mmd failed');
}
