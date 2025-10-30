from app import app, db
from models.order import Order


def debug_revenue():
    with app.app_context():
        try:
            print("=" * 50)
            print("🔍 DEBUGGING REVENUE CALCULATION")
            print("=" * 50)

            # Check if Order table exists
            print("1. Checking if Order table exists...")
            try:
                orders_count = Order.query.count()
                print(f"   ✅ Order table exists with {orders_count} orders")
            except Exception as e:
                print(f"   ❌ Order table error: {e}")
                return

            # Check all orders and their statuses
            print("\n2. Checking all orders...")
            all_orders = Order.query.all()

            if not all_orders:
                print("   ℹ️  No orders found in database")
                return

            # Print all orders with details
            total_all_orders = 0
            status_summary = {}

            for order in all_orders:
                status = order.status or 'no-status'
                amount = order.total_amount or 0

                # Add to status summary
                if status not in status_summary:
                    status_summary[status] = {'count': 0, 'revenue': 0}
                status_summary[status]['count'] += 1
                status_summary[status]['revenue'] += amount

                total_all_orders += amount

                print(f"   Order #{order.id}: status='{status}', amount=${amount:.2f}")

            # Print status summary
            print(f"\n3. Order Status Summary:")
            for status, data in status_summary.items():
                print(f"   {status}: {data['count']} orders, ${data['revenue']:.2f} revenue")

            # Check specifically for delivered orders
            print(f"\n4. Checking 'delivered' orders specifically...")
            delivered_orders = Order.query.filter_by(status='delivered').all()
            print(f"   Found {len(delivered_orders)} orders with status 'delivered'")

            delivered_revenue = 0
            for order in delivered_orders:
                amount = order.total_amount or 0
                delivered_revenue += amount
                print(f"   Order #{order.id}: ${amount:.2f}")

            print(f"   Total delivered revenue: ${delivered_revenue:.2f}")

            # Check for other completed statuses
            print(f"\n5. Checking other completed statuses...")
            completed_statuses = ['completed', 'shipped', 'paid', 'finished']
            alternative_revenue = 0
            alternative_orders = []

            for status in completed_statuses:
                orders = Order.query.filter_by(status=status).all()
                if orders:
                    status_revenue = sum(order.total_amount or 0 for order in orders)
                    alternative_revenue += status_revenue
                    alternative_orders.extend(orders)
                    print(f"   {status}: {len(orders)} orders, ${status_revenue:.2f}")

            print(f"   Total alternative revenue: ${alternative_revenue:.2f}")

            # Final summary
            print(f"\n6. FINAL SUMMARY:")
            print(f"   Total all orders revenue: ${total_all_orders:.2f}")
            print(f"   Delivered orders revenue: ${delivered_revenue:.2f}")
            print(f"   Alternative completed revenue: ${alternative_revenue:.2f}")
            print(
                f"   Recommended revenue to show: ${max(delivered_revenue, alternative_revenue, total_all_orders):.2f}")

        except Exception as e:
            print(f"❌ Debug error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    debug_revenue()