from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class User(AbstractUser):
    """Extended User model with role-based access"""
    
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('EMPLOYEE', 'Employee'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='EMPLOYEE')
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Fix for AbstractUser clash
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    class Meta:
        db_table = 'users'
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


class Company(models.Model):
    """Company model to manage different organizations"""
    
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    currency_code = models.CharField(max_length=10)  # e.g., USD, EUR, INR
    currency_symbol = models.CharField(max_length=10, blank=True, null=True)  # e.g., $, €, ₹
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'Companies'
        
    def __str__(self):
        return f"{self.name} ({self.currency_code})"


class ExpenseCategory(models.Model):
    """Expense categories for different types of expenses"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='expense_categories')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'expense_categories'
        verbose_name_plural = 'Expense Categories'
        unique_together = ('name', 'company')
        
    def __str__(self):
        return self.name


class Expense(models.Model):
    """Main expense model for employee expense claims"""
    
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )
    
    expense_number = models.CharField(max_length=50, unique=True)  # Auto-generated: EXP-2025-0001
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
    
    # Expense details
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency_code = models.CharField(max_length=10)  # Currency of the expense
    
    # Converted amount in company's default currency
    converted_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    conversion_rate = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    expense_date = models.DateField()
    merchant_name = models.CharField(max_length=255, blank=True, null=True)  # For OCR extraction
    
    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    current_approval_step = models.IntegerField(default=0)  # Tracks which approval step
    
    # Receipt management
    receipt_image = models.FileField(upload_to='receipts/%Y/%m/', blank=True, null=True)  # Changed to FileField
    receipt_ocr_data = models.JSONField(blank=True, null=True)  # Store OCR extracted data
    
    # Comments and notes
    employee_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'expenses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'employee']),
            models.Index(fields=['expense_number']),
            models.Index(fields=['company', 'status']),
        ]
        
    def __str__(self):
        return f"{self.expense_number} - {self.employee.get_full_name()} - {self.amount} {self.currency_code}"
    
    def save(self, *args, **kwargs):
        # Auto-generate expense number if not set
        if not self.expense_number:
            year = timezone.now().year
            last_expense = Expense.objects.filter(
                expense_number__startswith=f'EXP-{year}-'
            ).order_by('-expense_number').first()
            
            if last_expense:
                last_number = int(last_expense.expense_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.expense_number = f'EXP-{year}-{new_number:04d}'
        
        super().save(*args, **kwargs)


class ExpenseLine(models.Model):
    """Individual line items within an expense (for detailed breakdowns)"""
    
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, null=True, blank=True)
    
    class Meta:
        db_table = 'expense_lines'
        
    def __str__(self):
        return f"{self.expense.expense_number} - {self.description}"
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class ApprovalRule(models.Model):
    """Define approval rules for expenses"""
    
    RULE_TYPE_CHOICES = (
        ('SEQUENTIAL', 'Sequential Approval'),  # Multiple approvers in sequence
        ('PERCENTAGE', 'Percentage Based'),  # X% of approvers must approve
        ('SPECIFIC_APPROVER', 'Specific Approver'),  # Specific person can auto-approve
        ('HYBRID', 'Hybrid Rule'),  # Combination of percentage and specific approver
    )
    
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='approval_rules')
    rule_type = models.CharField(max_length=30, choices=RULE_TYPE_CHOICES)
    
    # Amount thresholds
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Category filter (optional)
    categories = models.ManyToManyField(ExpenseCategory, blank=True, related_name='approval_rules')
    
    # Percentage rule settings
    approval_percentage = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    
    # Manager approval flag
    requires_manager_approval = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)  # Higher priority rules are checked first
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'approval_rules'
        ordering = ['-priority', 'min_amount']
        
    def __str__(self):
        return f"{self.name} - {self.rule_type}"


class ApprovalStep(models.Model):
    """Define sequential approval steps for a rule"""
    
    approval_rule = models.ForeignKey(ApprovalRule, on_delete=models.CASCADE, related_name='approval_steps')
    step_number = models.IntegerField()  # Order of approval: 1, 2, 3...
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_steps')
    
    # For specific approver rules
    can_auto_approve = models.BooleanField(default=False)  # e.g., CFO can auto-approve
    
    class Meta:
        db_table = 'approval_steps'
        ordering = ['step_number']
        unique_together = ('approval_rule', 'step_number')
        
    def __str__(self):
        return f"{self.approval_rule.name} - Step {self.step_number} - {self.approver.get_full_name()}"


class ExpenseApproval(models.Model):
    """Track individual approval actions on expenses"""
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='approvals')
    approval_step = models.ForeignKey(ApprovalStep, on_delete=models.PROTECT, null=True, blank=True)
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approvals_given')
    
    step_number = models.IntegerField()  # Which step in the approval sequence
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    comments = models.TextField(blank=True, null=True)
    
    # Timestamps
    assigned_at = models.DateTimeField(auto_now_add=True)
    actioned_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'expense_approvals'
        ordering = ['step_number', 'assigned_at']
        unique_together = ('expense', 'step_number', 'approver')
        
    def __str__(self):
        return f"{self.expense.expense_number} - Step {self.step_number} - {self.approver.get_full_name()} - {self.status}"


class ExpenseComment(models.Model):
    """Comments on expenses (by employees, managers, admins)"""
    
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_comments')
    comment = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal comments not visible to employee
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'expense_comments'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.expense.expense_number} - Comment by {self.user.get_full_name()}"


class CurrencyExchangeRate(models.Model):
    """Cache currency exchange rates"""
    
    base_currency = models.CharField(max_length=10)
    target_currency = models.CharField(max_length=10)
    rate = models.DecimalField(max_digits=10, decimal_places=6)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'currency_exchange_rates'
        unique_together = ('base_currency', 'target_currency', 'date')
        indexes = [
            models.Index(fields=['base_currency', 'target_currency', 'date']),
        ]
        
    def __str__(self):
        return f"{self.base_currency} to {self.target_currency}: {self.rate} ({self.date})"


class AuditLog(models.Model):
    """Track all important actions in the system"""
    
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('SUBMIT', 'Submit'),
        ('CANCEL', 'Cancel'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)  # e.g., 'Expense', 'User'
    object_id = models.IntegerField()
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(blank=True, null=True)  # Additional data
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['model_name', 'object_id']),
        ]
        
    def __str__(self):
        return f"{self.action} - {self.model_name} - {self.user}"