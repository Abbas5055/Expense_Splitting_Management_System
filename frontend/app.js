const api = path => `/api${path}`;

async function apiFetch(path, opts){
  const res = await fetch(api(path), opts);
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || res.statusText);
  }
  return res.status === 204 ? null : res.json();
}

const groupsEl = document.getElementById('groups');
const groupTpl = document.getElementById('groupTpl');

document.getElementById('createGroup').addEventListener('click', async () => {
  const name = document.getElementById('groupName').value.trim();
  if (!name) return alert('Enter group name');
  await apiFetch('/groups', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name})});
  document.getElementById('groupName').value = '';
  loadGroups();
});

async function loadGroups(){
  try {
    const groups = await apiFetch('/groups');
    groupsEl.innerHTML = '';
    groups.forEach(g => renderGroup(g));
  } catch (e) {
    groupsEl.innerHTML = '<div style="color:tomato">Failed to load groups.</div>';
  }
}

function renderGroup(g){
  const node = groupTpl.content.cloneNode(true);
  const root = node.querySelector('.group');
  root.querySelector('.gname').textContent = g.name;
  const membersNode = root.querySelector('.members');
  const expensesNode = root.querySelector('.expenses');
  const balancesNode = root.querySelector('.balances');
  const memberInput = root.querySelector('.memberName');
  const addMemberBtn = root.querySelector('.addMember');
  const expTitle = root.querySelector('.expTitle');
  const expAmount = root.querySelector('.expAmount');
  const expPayer = root.querySelector('.expPayer');
  const equalCheck = root.querySelector('.equalSplit');
  const addExpenseBtn = root.querySelector('.addExpense');

  async function refreshMembers(){
    const members = await apiFetch(`/groups/${g.id}/members`);
    membersNode.innerHTML = '';
    expPayer.innerHTML = '';
    members.forEach(m => {
      const div = document.createElement('div'); div.className='item'; div.textContent = m.name; membersNode.appendChild(div);
      const opt = document.createElement('option'); opt.value = m.id; opt.textContent = m.name; expPayer.appendChild(opt);
    });
  }

  async function refreshExpenses(){
    const exps = await apiFetch(`/groups/${g.id}/expenses`);
    expensesNode.innerHTML = '';
    exps.forEach(e => {
      const div = document.createElement('div'); div.className='item';
      div.innerHTML = `<strong>${e.title || 'Expense'}</strong> — ${e.amount} (paid by ${e.payer_id})`;
      expensesNode.appendChild(div);
    });
  }

  async function refreshBalances(){
    const bals = await apiFetch(`/groups/${g.id}/balances`);
    balancesNode.innerHTML = '';
    bals.forEach(b => {
      const div = document.createElement('div'); div.className='item'; div.textContent = `${b.name}: ${b.balance}`;
      balancesNode.appendChild(div);
    });
  }

  addMemberBtn.addEventListener('click', async () => {
    const name = memberInput.value.trim(); if (!name) return;
    await apiFetch(`/groups/${g.id}/members`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name})});
    memberInput.value=''; await refreshMembers(); await refreshBalances();
  });

  addExpenseBtn.addEventListener('click', async () => {
    const title = expTitle.value.trim();
    const amount = parseFloat(expAmount.value);
    const payer_id = parseInt(expPayer.value);
    const equal_split = equalCheck.checked;
    if (!amount || !payer_id) return alert('Enter amount and payer');
    await apiFetch(`/groups/${g.id}/expenses`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({title, amount, payer_id, equal_split})});
    expTitle.value=''; expAmount.value=''; await refreshExpenses(); await refreshBalances();
  });

  root.querySelector('.gname').addEventListener('click', async () => {
    await refreshMembers(); await refreshExpenses(); await refreshBalances();
  });

  groupsEl.appendChild(node);
  // initial load
  refreshMembers(); refreshExpenses(); refreshBalances();
}

// initial
loadGroups();
