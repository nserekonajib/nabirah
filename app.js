// Application State
let expenses = [];
let capital = {
    totalCapital: 100000,
    availableCapital: 100000,
    totalExpenses: 0
};

// DOM Elements
const addExpenseBtn = document.getElementById('addExpenseBtn');
const addExpenseModal = document.getElementById('addExpenseModal');
const cancelExpenseBtn = document.getElementById('cancelExpenseBtn');
const expenseForm = document.getElementById('expenseForm');
const manageCapitalBtn = document.getElementById('manageCapitalBtn');
const capitalModal = document.getElementById('capitalModal');
const cancelCapitalBtn = document.getElementById('cancelCapitalBtn');
const addCapitalBtn = document.getElementById('addCapitalBtn');
const voucherModal = document.getElementById('voucherModal');
const closeVoucherBtn = document.getElementById('closeVoucherBtn');
const printVoucherBtn = document.getElementById('printVoucherBtn');
const searchInput = document.getElementById('searchInput');
const categoryFilter = document.getElementById('categoryFilter');
const sortSelect = document.getElementById('sortSelect');

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    loadData();
    updateDashboard();
    renderExpenseTable();
    setupEventListeners();
    
    // Set today's date as default
    document.getElementById('expenseDate').value = new Date().toISOString().split('T')[0];
});

// Event Listeners
function setupEventListeners() {
    addExpenseBtn.addEventListener('click', () => showModal(addExpenseModal));
    cancelExpenseBtn.addEventListener('click', () => hideModal(addExpenseModal));
    expenseForm.addEventListener('submit', handleAddExpense);
    
    manageCapitalBtn.addEventListener('click', () => {
        updateCapitalStatus();
        showModal(capitalModal);
    });
    cancelCapitalBtn.addEventListener('click', () => hideModal(capitalModal));
    addCapitalBtn.addEventListener('click', handleAddCapital);
    
    closeVoucherBtn.addEventListener('click', () => hideModal(voucherModal));
    printVoucherBtn.addEventListener('click', () => window.print());
    
    searchInput.addEventListener('input', renderExpenseTable);
    categoryFilter.addEventListener('change', renderExpenseTable);
    sortSelect.addEventListener('change', renderExpenseTable);
    
    // Check for overspending when amount changes
    document.getElementById('expenseAmount').addEventListener('input', checkOverspending);
    
    // Close modals when clicking outside
    [addExpenseModal, capitalModal, voucherModal].forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                hideModal(modal);
            }
        });
    });
}

// Modal Functions
function showModal(modal) {
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function hideModal(modal) {
    modal.classList.add('hidden');
    document.body.style.overflow = 'auto';
}

// Data Management
function loadData() {
    const savedExpenses = localStorage.getItem('expenses');
    const savedCapital = localStorage.getItem('capital');
    
    if (savedExpenses) {
        expenses = JSON.parse(savedExpenses);
    }
    
    if (savedCapital) {
        capital = JSON.parse(savedCapital);
    }
    
    // Recalculate totals
    const totalExpenses = expenses.reduce((sum, expense) => sum + expense.amount, 0);
    capital.totalExpenses = totalExpenses;
    capital.availableCapital = capital.totalCapital - totalExpenses;
    
    saveData();
}

function saveData() {
    localStorage.setItem('expenses', JSON.stringify(expenses));
    localStorage.setItem('capital', JSON.stringify(capital));
}

// Dashboard Functions
function updateDashboard() {
    const dashboard = document.getElementById('dashboard');
    const utilizationPercentage = (capital.totalExpenses / capital.totalCapital) * 100;
    const isOverspent = capital.availableCapital < 0;
    
    dashboard.innerHTML = `
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 slide-up">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-gray-600">Total Capital</p>
                    <p class="text-2xl font-bold text-gray-900">$${capital.totalCapital.toLocaleString()}</p>
                </div>
                <div class="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <i data-lucide="dollar-sign" class="h-6 w-6 text-blue-600"></i>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 slide-up">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-gray-600">Available Capital</p>
                    <p class="text-2xl font-bold ${isOverspent ? 'text-red-600' : 'text-emerald-600'}">
                        $${capital.availableCapital.toLocaleString()}
                    </p>
                </div>
                <div class="h-12 w-12 rounded-lg flex items-center justify-center ${isOverspent ? 'bg-red-100' : 'bg-emerald-100'}">
                    <i data-lucide="${isOverspent ? 'alert-triangle' : 'dollar-sign'}" class="h-6 w-6 ${isOverspent ? 'text-red-600' : 'text-emerald-600'}"></i>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 slide-up">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-gray-600">Total Expenses</p>
                    <p class="text-2xl font-bold text-gray-900">$${capital.totalExpenses.toLocaleString()}</p>
                </div>
                <div class="h-12 w-12 bg-orange-100 rounded-lg flex items-center justify-center">
                    <i data-lucide="trending-down" class="h-6 w-6 text-orange-600"></i>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 slide-up">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-gray-600">Utilization</p>
                    <p class="text-2xl font-bold ${utilizationPercentage > 90 ? 'text-red-600' : 'text-gray-900'}">
                        ${utilizationPercentage.toFixed(1)}%
                    </p>
                </div>
                <div class="h-12 w-12 rounded-lg flex items-center justify-center ${utilizationPercentage > 90 ? 'bg-red-100' : 'bg-purple-100'}">
                    <i data-lucide="bar-chart-3" class="h-6 w-6 ${utilizationPercentage > 90 ? 'text-red-600' : 'text-purple-600'}"></i>
                </div>
            </div>
            <div class="mt-4 w-full bg-gray-200 rounded-full h-2">
                <div class="h-2 rounded-full transition-all duration-300 ${utilizationPercentage > 90 ? 'bg-red-500' : 'bg-purple-500'}" 
                     style="width: ${Math.min(utilizationPercentage, 100)}%"></div>
            </div>
        </div>
    `;
    
    // Re-initialize icons for the dashboard
    lucide.createIcons();
}

// Expense Functions
function handleAddExpense(e) {
    e.preventDefault();
    
    // Clear previous errors
    clearErrors();
    
    // Get form data
    const formData = {
        date: document.getElementById('expenseDate').value,
        description: document.getElementById('expenseDescription').value.trim(),
        amount: parseFloat(document.getElementById('expenseAmount').value),
        category: document.getElementById('expenseCategory').value,
        payee: document.getElementById('expensePayee').value.trim(),
        approvedBy: document.getElementById('expenseApprovedBy').value.trim()
    };
    
    // Validate form
    if (!validateExpenseForm(formData)) {
        return;
    }
    
    // Create expense object
    const expense = {
        id: Date.now().toString(),
        date: formData.date,
        description: formData.description,
        amount: formData.amount,
        category: formData.category,
        payee: formData.payee,
        approvedBy: formData.approvedBy,
        voucherNumber: generateVoucherNumber(),
        createdAt: new Date().toISOString()
    };
    
    // Add expense
    expenses.push(expense);
    
    // Update capital
    capital.totalExpenses += expense.amount;
    capital.availableCapital = capital.totalCapital - capital.totalExpenses;
    
    // Save and update UI
    saveData();
    updateDashboard();
    renderExpenseTable();
    
    // Reset form and close modal
    expenseForm.reset();
    document.getElementById('expenseDate').value = new Date().toISOString().split('T')[0];
    hideModal(addExpenseModal);
    hideOverspendAlert();
}

function validateExpenseForm(data) {
    let isValid = true;
    
    if (!data.description) {
        showError('descriptionError', 'Description is required');
        isValid = false;
    }
    
    if (!data.amount || data.amount <= 0) {
        showError('amountError', 'Amount must be greater than 0');
        isValid = false;
    }
    
    if (!data.payee) {
        showError('payeeError', 'Payee is required');
        isValid = false;
    }
    
    if (!data.approvedBy) {
        showError('approvedByError', 'Approved by is required');
        isValid = false;
    }
    
    return isValid;
}

function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    errorElement.textContent = message;
    errorElement.classList.remove('hidden');
    
    // Add error styling to input
    const inputId = elementId.replace('Error', '');
    const input = document.getElementById('expense' + inputId.charAt(0).toUpperCase() + inputId.slice(1));
    if (input) {
        input.classList.add('border-red-500');
    }
}

function clearErrors() {
    const errorElements = ['descriptionError', 'amountError', 'payeeError', 'approvedByError'];
    errorElements.forEach(id => {
        const element = document.getElementById(id);
        element.classList.add('hidden');
        
        // Remove error styling from input
        const inputId = id.replace('Error', '');
        const input = document.getElementById('expense' + inputId.charAt(0).toUpperCase() + inputId.slice(1));
        if (input) {
            input.classList.remove('border-red-500');
        }
    });
}

function checkOverspending() {
    const amount = parseFloat(document.getElementById('expenseAmount').value) || 0;
    const wouldOverspend = capital.availableCapital - amount < 0;
    
    if (wouldOverspend && amount > 0) {
        showOverspendAlert(Math.abs(capital.availableCapital - amount));
    } else {
        hideOverspendAlert();
    }
}

function showOverspendAlert(overspendAmount) {
    const alert = document.getElementById('overspendAlert');
    const message = document.getElementById('overspendMessage');
    message.textContent = `This expense would exceed available capital by $${overspendAmount.toLocaleString()}`;
    alert.classList.remove('hidden');
}

function hideOverspendAlert() {
    document.getElementById('overspendAlert').classList.add('hidden');
}

function generateVoucherNumber() {
    const date = new Date();
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const time = String(Date.now()).slice(-4);
    return `EXP-${year}${month}${day}-${time}`;
}

// Capital Management
function updateCapitalStatus() {
    const statusDiv = document.getElementById('capitalStatus');
    statusDiv.innerHTML = `
        <div class="flex justify-between">
            <span>Total Capital:</span>
            <span class="font-semibold">$${capital.totalCapital.toLocaleString()}</span>
        </div>
        <div class="flex justify-between">
            <span>Total Expenses:</span>
            <span class="font-semibold">$${capital.totalExpenses.toLocaleString()}</span>
        </div>
        <div class="flex justify-between border-t pt-2">
            <span>Available Capital:</span>
            <span class="font-semibold ${capital.availableCapital < 0 ? 'text-red-600' : 'text-emerald-600'}">
                $${capital.availableCapital.toLocaleString()}
            </span>
        </div>
    `;
}

function handleAddCapital() {
    const amount = parseFloat(document.getElementById('newCapitalAmount').value);
    
    if (amount && amount > 0) {
        capital.totalCapital += amount;
        capital.availableCapital += amount;
        
        saveData();
        updateDashboard();
        updateCapitalStatus();
        
        document.getElementById('newCapitalAmount').value = '';
        hideModal(capitalModal);
    }
}

// Expense Table
function renderExpenseTable() {
    const container = document.getElementById('expenseTableContainer');
    const filteredExpenses = getFilteredExpenses();
    
    if (filteredExpenses.length === 0) {
        container.innerHTML = `
            <div class="p-8 text-center text-gray-500">
                <i data-lucide="receipt" class="h-12 w-12 mx-auto mb-4 text-gray-400"></i>
                <p>No expenses found matching your criteria.</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }
    
    const tableHTML = `
        <table class="w-full">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Voucher</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payee</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                ${filteredExpenses.map(expense => `
                    <tr class="hover:bg-gray-50 transition-colors duration-150">
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="flex items-center">
                                <i data-lucide="receipt" class="h-4 w-4 text-gray-400 mr-2"></i>
                                <span class="text-sm font-mono text-gray-900">${expense.voucherNumber}</span>
                            </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="flex items-center">
                                <i data-lucide="calendar" class="h-4 w-4 text-gray-400 mr-2"></i>
                                <span class="text-sm text-gray-900">${formatDate(expense.date)}</span>
                            </div>
                        </td>
                        <td class="px-6 py-4">
                            <div class="text-sm text-gray-900 max-w-xs truncate" title="${expense.description}">
                                ${expense.description}
                            </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(expense.category)}">
                                ${expense.category}
                            </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="flex items-center">
                                <i data-lucide="user" class="h-4 w-4 text-gray-400 mr-2"></i>
                                <span class="text-sm text-gray-900">${expense.payee}</span>
                            </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <div class="flex items-center">
                                <i data-lucide="dollar-sign" class="h-4 w-4 text-gray-400 mr-1"></i>
                                <span class="text-sm font-semibold text-gray-900">${expense.amount.toLocaleString()}</span>
                            </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <button onclick="showVoucher('${expense.id}')" class="text-blue-600 hover:text-blue-900 text-sm font-medium transition-colors duration-150">
                                View Voucher
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = tableHTML;
    lucide.createIcons();
}

function getFilteredExpenses() {
    const searchTerm = searchInput.value.toLowerCase();
    const selectedCategory = categoryFilter.value;
    const [sortBy, sortOrder] = sortSelect.value.split('-');
    
    let filtered = expenses.filter(expense => {
        const matchesSearch = expense.description.toLowerCase().includes(searchTerm) ||
                            expense.payee.toLowerCase().includes(searchTerm) ||
                            expense.voucherNumber.toLowerCase().includes(searchTerm);
        
        const matchesCategory = selectedCategory === 'All' || expense.category === selectedCategory;
        
        return matchesSearch && matchesCategory;
    });
    
    // Sort expenses
    filtered.sort((a, b) => {
        let aValue, bValue;
        
        switch (sortBy) {
            case 'date':
                aValue = new Date(a.date);
                bValue = new Date(b.date);
                break;
            case 'amount':
                aValue = a.amount;
                bValue = b.amount;
                break;
            case 'description':
                aValue = a.description.toLowerCase();
                bValue = b.description.toLowerCase();
                break;
            default:
                return 0;
        }
        
        if (sortOrder === 'asc') {
            return aValue > bValue ? 1 : -1;
        } else {
            return aValue < bValue ? 1 : -1;
        }
    });
    
    return filtered;
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

function getCategoryColor(category) {
    const colors = {
        'Office Supplies': 'bg-blue-100 text-blue-800',
        'Travel': 'bg-green-100 text-green-800',
        'Utilities': 'bg-yellow-100 text-yellow-800',
        'Equipment': 'bg-purple-100 text-purple-800',
        'Professional Services': 'bg-indigo-100 text-indigo-800',
        'Marketing': 'bg-pink-100 text-pink-800',
        'Insurance': 'bg-red-100 text-red-800',
        'Miscellaneous': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
}

// Voucher Functions
function showVoucher(expenseId) {
    const expense = expenses.find(e => e.id === expenseId);
    if (!expense) return;
    
    const voucherContent = document.getElementById('voucherContent');
    voucherContent.innerHTML = generateVoucherHTML(expense);
    
    showModal(voucherModal);
    lucide.createIcons();
}

function generateVoucherHTML(expense) {
    return `
        <!-- Company Header -->
        <div class="text-center mb-8 border-b-2 border-gray-300 pb-6 print:break-inside-avoid">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">ACME Corporation</h1>
            <p class="text-gray-600">123 Business Street, City, State 12345</p>
            <p class="text-gray-600">Phone: (555) 123-4567 | Email: info@acmecorp.com</p>
            <h2 class="text-xl font-semibold text-gray-800 mt-4">EXPENSE VOUCHER</h2>
        </div>

        <!-- Voucher Details -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8 print:break-inside-avoid">
            <div>
                <h3 class="text-lg font-semibold text-gray-800 mb-4">Voucher Information</h3>
                <div class="space-y-3">
                    <div class="flex">
                        <span class="font-medium text-gray-700 w-32">Voucher No:</span>
                        <span class="text-gray-900 font-mono">${expense.voucherNumber}</span>
                    </div>
                    <div class="flex">
                        <span class="font-medium text-gray-700 w-32">Date:</span>
                        <span class="text-gray-900">${formatDateLong(expense.date)}</span>
                    </div>
                    <div class="flex">
                        <span class="font-medium text-gray-700 w-32">Category:</span>
                        <span class="text-gray-900">${expense.category}</span>
                    </div>
                </div>
            </div>

            <div>
                <h3 class="text-lg font-semibold text-gray-800 mb-4">Payment Details</h3>
                <div class="space-y-3">
                    <div class="flex">
                        <span class="font-medium text-gray-700 w-32">Payee:</span>
                        <span class="text-gray-900">${expense.payee}</span>
                    </div>
                    <div class="flex">
                        <span class="font-medium text-gray-700 w-32">Amount:</span>
                        <span class="text-gray-900 font-semibold text-xl">$${expense.amount.toLocaleString()}</span>
                    </div>
                    <div class="flex">
                        <span class="font-medium text-gray-700 w-32">Approved By:</span>
                        <span class="text-gray-900">${expense.approvedBy}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Description -->
        <div class="mb-8 print:break-inside-avoid">
            <h3 class="text-lg font-semibold text-gray-800 mb-4">Description</h3>
            <div class="bg-gray-50 p-4 rounded-lg border">
                <p class="text-gray-900">${expense.description}</p>
            </div>
        </div>

        <!-- Amount in Words -->
        <div class="mb-8 print:break-inside-avoid">
            <h3 class="text-lg font-semibold text-gray-800 mb-4">Amount in Words</h3>
            <div class="bg-gray-50 p-4 rounded-lg border">
                <p class="text-gray-900 font-medium">${numberToWords(expense.amount)} Dollars Only</p>
            </div>
        </div>

        <!-- Signatures -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12 print:break-inside-avoid">
            <div class="text-center">
                <div class="border-t border-gray-400 pt-2 mt-16">
                    <p class="text-sm text-gray-600">Prepared By</p>
                    <p class="text-sm text-gray-500 mt-1">Date: ${formatDateLong(expense.createdAt)}</p>
                </div>
            </div>
            <div class="text-center">
                <div class="border-t border-gray-400 pt-2 mt-16">
                    <p class="text-sm text-gray-600">Approved By</p>
                    <p class="text-sm font-medium text-gray-900">${expense.approvedBy}</p>
                </div>
            </div>
            <div class="text-center">
                <div class="border-t border-gray-400 pt-2 mt-16">
                    <p class="text-sm text-gray-600">Received By</p>
                    <p class="text-sm font-medium text-gray-900">${expense.payee}</p>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="mt-12 pt-6 border-t border-gray-200 text-center print:break-inside-avoid">
            <p class="text-xs text-gray-500">This voucher is computer generated and does not require a signature.</p>
            <p class="text-xs text-gray-500 mt-1">Generated on: ${new Date().toLocaleString()}</p>
        </div>
    `;
}

function formatDateLong(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Number to Words Conversion
function numberToWords(num) {
    const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];
    const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
    const teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
    
    if (num === 0) return 'Zero';
    
    function convertHundreds(n) {
        let result = '';
        
        if (n >= 100) {
            result += ones[Math.floor(n / 100)] + ' Hundred ';
            n %= 100;
        }
        
        if (n >= 20) {
            result += tens[Math.floor(n / 10)] + ' ';
            n %= 10;
        } else if (n >= 10) {
            result += teens[n - 10] + ' ';
            return result;
        }
        
        if (n > 0) {
            result += ones[n] + ' ';
        }
        
        return result;
    }
    
    let integerPart = Math.floor(num);
    const decimalPart = Math.round((num - integerPart) * 100);
    
    let result = '';
    
    if (integerPart >= 1000000) {
        result += convertHundreds(Math.floor(integerPart / 1000000)) + 'Million ';
        integerPart %= 1000000;
    }
    
    if (integerPart >= 1000) {
        result += convertHundreds(Math.floor(integerPart / 1000)) + 'Thousand ';
        integerPart %= 1000;
    }
    
    if (integerPart > 0) {
        result += convertHundreds(integerPart);
    }
    
    if (decimalPart > 0) {
        result += 'and ' + convertHundreds(decimalPart) + 'Cents ';
    }
    
    return result.trim();
}